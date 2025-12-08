#!/usr/bin/env python3
"""Simple test to verify tool calling format with Ollama"""

import asyncio
import os
from pathlib import Path
import sys

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from dotenv import load_dotenv
from dr_agent.client import LLMToolClient
from dr_agent.tool_interface.base import BaseTool

# Simple test tool that echoes back its input
class TestTool(BaseTool):
    def __init__(self, **kwargs):
        super().__init__(
            name="test_tool",
            description="A simple test tool",
            tool_parser="v20250824",
            **kwargs
        )

    async def __call__(self, query: str) -> str:
        return f"Tool received: {query}"

    def _format_output(self, output) -> str:
        return output

    def _generate_tool_schema(self):
        return {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A simple test tool that echoes back input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The input to echo back"
                        }
                    },
                    "required": ["query"]
                }
            }
        }

async def test_native_tool_calling():
    # Load environment
    load_dotenv(".env.ollama")
    os.environ.setdefault("OPENAI_API_KEY", "ollama")

    # Create client with test tool
    tool = TestTool()

    client = LLMToolClient(
        model_name="cow/tulu3_tools:8b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        tools=[tool]
    )

    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "Use the test_tool to echo the message 'Hello from tool calling'"}
    ]

    print("\n=== Testing Native Tool Calling ===")
    print(f"Model: cow/tulu3_tools:8b")
    print(f"Base URL: http://localhost:11434/v1")
    print("\nUser message: Use the test_tool to echo the message 'Hello from tool calling'")
    print("\nGenerating response...\n")

    result = await client.generate_with_tools(
        prompt_or_messages=messages,
        tool_calling_mode="native",
        verbose=True
    )

    print(f"\n=== Result ===")
    print(f"Generated text: {result.generated_text}")
    print(f"Tool calls made: {result.tool_call_count}")
    print(f"Stopped reason: {result.stopped_reason}")

    for i, tool_call in enumerate(result.tool_calls):
        print(f"\nTool call {i+1}:")
        print(f"  Tool name: {tool_call.tool_name}")
        print(f"  Called: {tool_call.called}")
        print(f"  Output: {tool_call.output}")
        print(f"  Error: {tool_call.error}")

if __name__ == "__main__":
    asyncio.run(test_native_tool_calling())