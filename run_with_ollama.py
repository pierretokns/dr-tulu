#!/usr/bin/env python3
"""
Run DR-Tulu with Ollama as the LLM backend (with tool calling support)
Usage: python run_with_ollama.py --query "Your research query"
"""

import os
import sys
import argparse
from pathlib import Path

# Load Ollama environment variables
env_file = Path(__file__).parent / ".env.ollama"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"').strip("'")
    print("✓ Loaded Ollama environment configuration")

# Now import after env vars are set
sys.path.insert(0, str(Path(__file__).parent / "agent/dr_agent/client_adapters"))

from ollama_openai_adapter import create_ollama_adapter

def main():
    parser = argparse.ArgumentParser(description="DR-Tulu with Ollama")
    parser.add_argument("--query", "-q", required=True, help="Research query")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Max response tokens")
    parser.add_argument("--temperature", type=float, default=0.7, help="Model temperature")
    parser.add_argument("--tools", action="store_true", help="Enable tool calling")
    
    args = parser.parse_args()
    
    print(f"\n🔍 DR-Tulu + Ollama Research Agent (Tool Calling: {'Enabled' if args.tools else 'Disabled'})")
    print("=" * 60)
    
    # Initialize adapter
    adapter = create_ollama_adapter()
    print(f"✓ Model: {adapter.model}")
    print(f"✓ Endpoint: {adapter.base_url}")
    print()
    print(f"Query: {args.query}")
    print("-" * 60)
    
    # Define sample tools if requested
    tools = None
    if args.tools:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_papers",
                    "description": "Search academic papers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results", "default": 10}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    # Make request
    try:
        response = adapter.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert research assistant. Provide detailed, well-sourced answers."
                },
                {
                    "role": "user",
                    "content": args.query
                }
            ],
            tools=tools if args.tools else None,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
        
        # Print response
        print("\nResponse:")
        print("-" * 60)
        print(response.choices[0].message.content)
        
        # Check for tool calls
        if args.tools and hasattr(response.choices[0].message, 'tool_calls'):
            if response.choices[0].message.tool_calls:
                print("\n" + "-" * 60)
                print("Tool Calls Made:")
                for tc in response.choices[0].message.tool_calls:
                    print(f"  • {tc.function.name}")
                    print(f"    Arguments: {tc.function.arguments}")
        
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Ollama running? (ollama serve)")
        print("  2. Is model loaded? (ollama list)")
        print("  3. Check endpoint: curl http://localhost:11434/api/tags")
        print("  4. Check template: ollama show tulu3_tools")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())