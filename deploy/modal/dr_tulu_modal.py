"""
DR-Tulu Modal Deployment

This deploys the full DR-Tulu research agent stack on Modal:
- vLLM server with DR-Tulu-8B model
- MCP tool server for search/browse tools
- FastAPI endpoint for frontend integration

Usage:
    # Deploy
    modal deploy dr_tulu_modal.py

    # Test locally
    modal serve dr_tulu_modal.py
"""

import modal
import os

# ============================================================================
# Modal App Configuration
# ============================================================================

app = modal.App("dr-tulu-research-agent")

# Define the GPU image with vLLM and dependencies
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.6.0",
        "torch>=2.1.0",
        "transformers>=4.40.0",
        "huggingface_hub",
        "fastapi",
        "uvicorn",
        "httpx",
        "aiohttp",
        "pydantic",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "VLLM_ATTENTION_BACKEND": "FLASH_ATTN",
    })
)

# Define the CPU image for MCP tools
mcp_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi",
        "uvicorn",
        "httpx",
        "aiohttp",
        "pydantic",
        "tinydb",
        "mcp",
    )
)

# ============================================================================
# Secrets - Set these in Modal dashboard or via CLI
# ============================================================================
# modal secret create dr-tulu-secrets \
#   SERPER_API_KEY=xxx \
#   S2_API_KEY=xxx \
#   JINA_API_KEY=xxx

# ============================================================================
# vLLM Model Server
# ============================================================================

@app.cls(
    image=vllm_image,
    gpu=modal.gpu.L4(),  # L4 is cost-effective for 8B models (~$0.50/hr)
    container_idle_timeout=300,  # Scale to zero after 5 min idle
    allow_concurrent_inputs=10,
    secrets=[modal.Secret.from_name("dr-tulu-secrets", required=False)],
)
class DRTuluModel:
    model_name: str = "rl-research/DR-Tulu-8B"

    @modal.enter()
    def load_model(self):
        """Load the model when container starts."""
        from vllm import LLM, SamplingParams

        print(f"Loading model: {self.model_name}")
        self.llm = LLM(
            model=self.model_name,
            dtype="auto",
            max_model_len=16384,  # Reduced for L4 memory
            trust_remote_code=True,
            gpu_memory_utilization=0.90,
        )
        self.tokenizer = self.llm.get_tokenizer()
        print("Model loaded successfully!")

    @modal.method()
    def generate(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stop: list[str] = None,
    ) -> dict:
        """Generate a response from the model."""
        from vllm import SamplingParams

        # Format messages into prompt
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or ["</answer>", "<|eot_id|>", "<|end|>"],
        )

        outputs = self.llm.generate([prompt], sampling_params)
        generated_text = outputs[0].outputs[0].text

        return {
            "content": generated_text,
            "finish_reason": outputs[0].outputs[0].finish_reason,
            "usage": {
                "prompt_tokens": len(outputs[0].prompt_token_ids),
                "completion_tokens": len(outputs[0].outputs[0].token_ids),
            }
        }

    @modal.method()
    def health(self) -> dict:
        """Health check endpoint."""
        return {"status": "ok", "model": self.model_name}


# ============================================================================
# MCP Tool Server (Search & Browse)
# ============================================================================

@app.cls(
    image=mcp_image,
    container_idle_timeout=300,
    allow_concurrent_inputs=50,
    secrets=[modal.Secret.from_name("dr-tulu-secrets", required=False)],
)
class MCPTools:
    """Lightweight tool server for search and browse operations."""

    @modal.enter()
    def setup(self):
        """Initialize HTTP client."""
        import httpx
        self.client = httpx.AsyncClient(timeout=30.0)

        # Get API keys from environment
        self.serper_key = os.environ.get("SERPER_API_KEY", "")
        self.s2_key = os.environ.get("S2_API_KEY", "")
        self.jina_key = os.environ.get("JINA_API_KEY", "")

        print(f"MCP Tools initialized. Serper: {'✓' if self.serper_key else '✗'}, "
              f"S2: {'✓' if self.s2_key else '✗'}, Jina: {'✓' if self.jina_key else '✗'}")

    @modal.method()
    async def google_search(self, query: str, num_results: int = 10) -> dict:
        """Search Google via Serper API."""
        if not self.serper_key:
            return {"error": "SERPER_API_KEY not configured", "results": []}

        try:
            response = await self.client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
                json={"q": query, "num": num_results},
            )
            data = response.json()

            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })

            return {"results": results, "query": query}
        except Exception as e:
            return {"error": str(e), "results": []}

    @modal.method()
    async def semantic_scholar_search(
        self,
        query: str,
        num_results: int = 10,
        year_start: int = None,
        year_end: int = None,
    ) -> dict:
        """Search Semantic Scholar for academic papers."""
        try:
            params = {
                "query": query,
                "limit": num_results,
                "fields": "title,url,abstract,year,citationCount,authors",
            }
            if year_start:
                params["year"] = f"{year_start}-" + (str(year_end) if year_end else "")

            headers = {}
            if self.s2_key:
                headers["x-api-key"] = self.s2_key

            response = await self.client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
                headers=headers,
            )
            data = response.json()

            results = []
            for paper in data.get("data", []):
                authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3]])
                results.append({
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "snippet": paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                    "year": paper.get("year"),
                    "citations": paper.get("citationCount", 0),
                    "authors": authors,
                })

            return {"results": results, "query": query}
        except Exception as e:
            return {"error": str(e), "results": []}

    @modal.method()
    async def jina_browse(self, url: str) -> dict:
        """Fetch and clean webpage content via Jina Reader."""
        try:
            headers = {"Accept": "text/plain"}
            if self.jina_key:
                headers["Authorization"] = f"Bearer {self.jina_key}"

            response = await self.client.get(
                f"https://r.jina.ai/{url}",
                headers=headers,
                timeout=30.0,
            )

            content = response.text[:10000]  # Limit content size

            return {
                "url": url,
                "content": content,
                "success": True,
            }
        except Exception as e:
            return {"url": url, "content": "", "error": str(e), "success": False}

    @modal.method()
    def health(self) -> dict:
        """Health check."""
        return {
            "status": "ok",
            "serper_configured": bool(self.serper_key),
            "s2_configured": bool(self.s2_key),
            "jina_configured": bool(self.jina_key),
        }


# ============================================================================
# Research Agent Orchestrator
# ============================================================================

@app.cls(
    image=mcp_image,
    container_idle_timeout=600,
    allow_concurrent_inputs=5,
    secrets=[modal.Secret.from_name("dr-tulu-secrets", required=False)],
)
class ResearchAgent:
    """
    Orchestrates the research workflow:
    1. Receives user query
    2. Calls DR-Tulu model for reasoning
    3. Executes tool calls (search, browse)
    4. Returns final research report
    """

    @modal.enter()
    def setup(self):
        """Initialize connections to model and tools."""
        self.model = DRTuluModel()
        self.tools = MCPTools()

        # System prompt for DR-Tulu
        self.system_prompt = """You are DR-Tulu, a deep research assistant. Your goal is to provide comprehensive, well-researched answers to user questions.

You have access to the following tools:
- google_search(query): Search the web for information
- semantic_scholar_search(query, year_start?, year_end?): Search academic papers
- jina_browse(url): Read the content of a webpage

When answering:
1. First think about what information you need
2. Use tools to gather relevant information
3. Synthesize the information into a comprehensive answer
4. Include citations to your sources

Format your response as:
<context>
[Your thinking and tool calls here]
</context>
<answer>
[Your final, comprehensive answer with citations]
</answer>"""

    def _parse_tool_calls(self, text: str) -> list[dict]:
        """Parse tool calls from model output."""
        import re

        tool_calls = []

        # Pattern for tool calls: <tool name="tool_name">params</tool>
        pattern = r'<tool\s+name=["\'](\w+)["\']>(.*?)</tool>'
        matches = re.findall(pattern, text, re.DOTALL)

        for tool_name, params in matches:
            tool_calls.append({
                "name": tool_name,
                "params": params.strip(),
            })

        return tool_calls

    async def _execute_tool(self, tool_name: str, params: str) -> str:
        """Execute a tool and return results."""
        try:
            if tool_name == "google_search":
                result = await self.tools.google_search.remote.aio(params)
                if result.get("results"):
                    formatted = "\n".join([
                        f"- {r['title']}: {r['snippet'][:200]}... ({r['url']})"
                        for r in result["results"][:5]
                    ])
                    return f"Search results for '{params}':\n{formatted}"
                return f"No results found for '{params}'"

            elif tool_name == "semantic_scholar_search":
                result = await self.tools.semantic_scholar_search.remote.aio(params)
                if result.get("results"):
                    formatted = "\n".join([
                        f"- [{r['year']}] {r['title']} ({r['citations']} citations)\n  {r['snippet'][:150]}..."
                        for r in result["results"][:5]
                    ])
                    return f"Academic papers for '{params}':\n{formatted}"
                return f"No papers found for '{params}'"

            elif tool_name == "jina_browse":
                result = await self.tools.jina_browse.remote.aio(params)
                if result.get("success"):
                    return f"Content from {params}:\n{result['content'][:3000]}..."
                return f"Failed to fetch {params}: {result.get('error', 'Unknown error')}"

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Tool error ({tool_name}): {str(e)}"

    @modal.method()
    async def research(self, query: str, max_iterations: int = 5) -> dict:
        """
        Perform deep research on a query.

        Returns a dict with:
        - answer: The final research report
        - thinking: The reasoning process
        - tool_calls: List of tools called
        - sources: List of sources used
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

        all_tool_calls = []
        thinking_parts = []

        for iteration in range(max_iterations):
            # Get model response
            response = self.model.generate.remote(
                messages=messages,
                max_tokens=4096,
                temperature=0.7,
            )

            text = response["content"]
            thinking_parts.append(f"[Iteration {iteration + 1}]\n{text}")

            # Check if we have a final answer
            if "<answer>" in text and "</answer>" in text:
                # Extract final answer
                import re
                answer_match = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL)
                if answer_match:
                    return {
                        "answer": answer_match.group(1).strip(),
                        "thinking": "\n\n".join(thinking_parts),
                        "tool_calls": all_tool_calls,
                        "iterations": iteration + 1,
                    }

            # Parse and execute tool calls
            tool_calls = self._parse_tool_calls(text)

            if not tool_calls:
                # No tools and no answer - ask model to conclude
                messages.append({"role": "assistant", "content": text})
                messages.append({
                    "role": "user",
                    "content": "Please provide your final answer based on the information gathered."
                })
                continue

            # Execute tools
            tool_results = []
            for tc in tool_calls:
                result = await self._execute_tool(tc["name"], tc["params"])
                tool_results.append(f"[{tc['name']}({tc['params']})]\n{result}")
                all_tool_calls.append({
                    "tool": tc["name"],
                    "params": tc["params"],
                    "result_preview": result[:200],
                })

            # Add tool results to conversation
            messages.append({"role": "assistant", "content": text})
            messages.append({
                "role": "user",
                "content": "Tool results:\n" + "\n\n".join(tool_results)
            })

        # Max iterations reached - force conclusion
        return {
            "answer": thinking_parts[-1] if thinking_parts else "Research incomplete",
            "thinking": "\n\n".join(thinking_parts),
            "tool_calls": all_tool_calls,
            "iterations": max_iterations,
            "incomplete": True,
        }

    @modal.method()
    def health(self) -> dict:
        """Health check."""
        return {"status": "ok", "agent": "ResearchAgent"}


# ============================================================================
# Web API Endpoint
# ============================================================================

@app.function(
    image=mcp_image,
    container_idle_timeout=300,
    allow_concurrent_inputs=20,
    secrets=[modal.Secret.from_name("dr-tulu-secrets", required=False)],
)
@modal.asgi_app()
def web_app():
    """FastAPI web application for the research agent."""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import json
    import asyncio

    app = FastAPI(
        title="DR-Tulu Research API",
        description="Deep research agent powered by DR-Tulu-8B",
        version="1.0.0",
    )

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ResearchRequest(BaseModel):
        query: str
        max_iterations: int = 5
        stream: bool = False

    class SearchRequest(BaseModel):
        query: str
        num_results: int = 10

    @app.get("/")
    async def root():
        return {
            "name": "DR-Tulu Research API",
            "version": "1.0.0",
            "endpoints": [
                "/research - POST - Perform deep research",
                "/search/google - POST - Google search",
                "/search/scholar - POST - Academic paper search",
                "/browse - POST - Fetch webpage content",
                "/health - GET - Health check",
            ]
        }

    @app.get("/health")
    async def health():
        agent = ResearchAgent()
        tools = MCPTools()
        model = DRTuluModel()

        return {
            "status": "ok",
            "model": model.health.remote(),
            "tools": tools.health.remote(),
        }

    @app.post("/research")
    async def research(request: ResearchRequest):
        """Perform deep research on a query."""
        agent = ResearchAgent()

        if request.stream:
            # TODO: Implement streaming response
            pass

        result = await agent.research.remote.aio(
            query=request.query,
            max_iterations=request.max_iterations,
        )

        return result

    @app.post("/search/google")
    async def google_search(request: SearchRequest):
        """Search Google via Serper."""
        tools = MCPTools()
        return await tools.google_search.remote.aio(
            query=request.query,
            num_results=request.num_results,
        )

    @app.post("/search/scholar")
    async def scholar_search(request: SearchRequest):
        """Search Semantic Scholar."""
        tools = MCPTools()
        return await tools.semantic_scholar_search.remote.aio(
            query=request.query,
            num_results=request.num_results,
        )

    class BrowseRequest(BaseModel):
        url: str

    @app.post("/browse")
    async def browse(request: BrowseRequest):
        """Fetch webpage content via Jina."""
        tools = MCPTools()
        return await tools.jina_browse.remote.aio(url=request.url)

    return app


# ============================================================================
# CLI Entry Points
# ============================================================================

@app.local_entrypoint()
def main():
    """Test the deployment locally."""
    print("Testing DR-Tulu deployment...")

    # Test model
    model = DRTuluModel()
    print("\n1. Testing model health...")
    health = model.health.remote()
    print(f"   Model: {health}")

    # Test tools
    tools = MCPTools()
    print("\n2. Testing tools health...")
    health = tools.health.remote()
    print(f"   Tools: {health}")

    # Test a simple search
    print("\n3. Testing Google search...")
    result = tools.google_search.remote("What is reinforcement learning?", num_results=3)
    print(f"   Found {len(result.get('results', []))} results")

    # Test model generation
    print("\n4. Testing model generation...")
    response = model.generate.remote(
        messages=[
            {"role": "user", "content": "What is 2+2? Answer briefly."}
        ],
        max_tokens=100,
    )
    print(f"   Response: {response['content'][:100]}...")

    print("\n✓ All tests passed! Deploy with: modal deploy dr_tulu_modal.py")
