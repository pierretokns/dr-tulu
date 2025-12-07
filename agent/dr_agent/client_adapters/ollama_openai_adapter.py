"""
Ollama OpenAI-Compatible Adapter for DR-Tulu
Allows Ollama to be used as if it's an OpenAI endpoint
Includes tool calling support with Tulu 3 JSON parsing
"""

from openai import OpenAI, AsyncOpenAI
import os
import re
import json
from typing import Optional, List, Dict, Any

class TuluToolCallParser:
    """Parse Tulu 3's tool calling format (JSON)"""
    
    @staticmethod
    def extract_tool_calls(content: str) -> List[Dict[str, Any]]:
        """
        Extract JSON tool calls from Tulu 3 model response
        
        Tulu 3 outputs: {"name": "function_name", "parameters": {...}}
        
        Args:
            content: Model response text
            
        Returns:
            List of tool call dicts with 'name' and 'parameters'
        """
        tool_calls = []
        
        # Pattern to match: {"name": "...", "parameters": {...}}
        # Handles whitespace variations in JSON
        pattern = r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"parameters"\s*:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})\s*\}'
        
        matches = re.finditer(pattern, content)
        for match in matches:
            try:
                func_name = match.group(1)
                params_str = match.group(2)
                parameters = json.loads(params_str)
                
                tool_calls.append({
                    "name": func_name,
                    "parameters": parameters
                })
            except (json.JSONDecodeError, IndexError) as e:
                # Log but don't fail - allow partial parsing
                print(f"Warning: Could not parse tool call: {e}")
                continue
        
        return tool_calls
    
    @staticmethod
    def format_tool_calls_for_openai(tool_calls: List[Dict]) -> List[Dict]:
        """
        Convert extracted tool calls to OpenAI SDK format
        
        Args:
            tool_calls: List of tool call dicts
            
        Returns:
            List formatted for OpenAI SDK
        """
        formatted = []
        for i, tc in enumerate(tool_calls):
            formatted.append({
                "id": f"call_{i}",
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc["parameters"])
                }
            })
        return formatted

class OllamaOpenAIAdapter:
    """Adapter to use Ollama as OpenAI-compatible endpoint with tool calling"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "tulu3_tools",
        api_key: str = "ollama"
    ):
        """
        Initialize Ollama OpenAI adapter
        
        Args:
            base_url: Ollama API endpoint (default: localhost:11434/v1)
            model: Model name in Ollama (default: tulu3_tools)
            api_key: Dummy API key (Ollama doesn't validate this)
        """
        self.base_url = base_url or "http://localhost:11434/v1"
        self.model = model or "tulu3_tools"
        self.api_key = api_key or "ollama"
        self.parser = TuluToolCallParser()
        
        # Initialize sync and async clients
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.async_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def _process_tool_calls(self, response: Any) -> Any:
        """
        Post-process response to extract tool calls from content
        
        Tulu 3 outputs tool calls in content as JSON.
        This method extracts them and converts to OpenAI format.
        """
        if not response or not response.choices:
            return response
        
        choice = response.choices[0]
        
        # Check if content contains tool calls
        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            content = choice.message.content
            if content and '{' in content and '"name"' in content:
                # Try to extract tool calls
                tool_calls = self.parser.extract_tool_calls(content)
                if tool_calls:
                    # Convert to OpenAI format
                    formatted_calls = self.parser.format_tool_calls_for_openai(tool_calls)
                    choice.message.tool_calls = formatted_calls
        
        return response
    
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Synchronous chat completion with tool calling support
        
        Args:
            messages: Message history
            tools: Tool definitions for tool calling
            temperature: Model temperature
            max_tokens: Max tokens in response
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            OpenAI response dict
        """
        request_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
            
        if tools:
            request_kwargs["tools"] = tools
        
        request_kwargs.update(kwargs)
        
        response = self.client.chat.completions.create(**request_kwargs)
        
        # Post-process to extract tool calls from content
        response = self._process_tool_calls(response)
        
        return response
    
    async def async_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Asynchronous chat completion with tool calling support
        
        Args:
            messages: Message history
            tools: Tool definitions for tool calling
            temperature: Model temperature
            max_tokens: Max tokens in response
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            OpenAI response dict
        """
        request_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
            
        if tools:
            request_kwargs["tools"] = tools
        
        request_kwargs.update(kwargs)
        
        response = await self.async_client.chat.completions.create(**request_kwargs)
        
        # Post-process to extract tool calls from content
        response = self._process_tool_calls(response)
        
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model and capabilities"""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "type": "Ollama (OpenAI-compatible)",
            "supports_tools": True,
            "tool_calling_format": "Tulu 3 JSON (cow/tulu3_tools compatible)",
            "parser": "TuluToolCallParser"
        }

# Factory function for easy initialization
def create_ollama_adapter(
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> OllamaOpenAIAdapter:
    """
    Create an Ollama adapter with environment variable support
    
    Environment variables:
    - OLLAMA_BASE_URL: Ollama API endpoint (default: http://localhost:11434/v1)
    - OLLAMA_MODEL: Model name (default: tulu3_tools)
    - OPENAI_API_KEY: Can be set to 'ollama' to avoid validation
    """
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = model or os.getenv("OLLAMA_MODEL", "tulu3_tools")
    
    return OllamaOpenAIAdapter(
        base_url=base_url,
        model=model,
        api_key="ollama"
    )
