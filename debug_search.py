#!/usr/bin/env python3
"""Debug script to test tool calling with the search workflow"""

import asyncio
import os
from pathlib import Path
import sys

# Add the agent directory to the path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from dr_agent.workflow import load_config
from workflows.auto_search_sft import AutoReasonSearchWorkflow

async def test_search():
    # Load the ollama-specific workflow configuration
    config_dict = load_config("agent/workflows/auto_search_sft-ollama.yaml")
    workflow = AutoReasonSearchWorkflow(config_dict)

    # Test with a query that requires searching
    query = "What is the population of Tokyo in 2024?"

    print(f"\n=== Testing Search Query ===")
    print(f"Query: {query}")
    print(f"Model: {workflow.configuration.search_agent_model_name}")
    print(f"Tool calling mode: {workflow.configuration.tool_calling_mode}")
    print(f"Tool parser: {workflow.configuration.tool_parser}")
    print(f"Browse tool: {workflow.configuration.browse_tool_name}")
    print(f"Base URL: {workflow.configuration.search_agent_base_url}")
    print("\n")

    # Run the search
    result = await workflow(
        problem=query,
        dataset_name="simpleqa",  # Valid dataset name
        verbose=True
    )

    print("\n=== Search Result ===")
    print(f"Final response: {result.get('final_response', 'No response')}")
    print(f"Total tool calls: {result.get('total_tool_calls', 0)}")
    print(f"Searched links: {result.get('searched_links', [])}")
    print(f"Browsed links: {result.get('browsed_links', [])}")

if __name__ == "__main__":
    # Load environment variables from .env.ollama
    from dotenv import load_dotenv
    load_dotenv(".env.ollama")

    # Set additional environment variables
    os.environ.setdefault("OPENAI_API_KEY", "ollama")

    asyncio.run(test_search())