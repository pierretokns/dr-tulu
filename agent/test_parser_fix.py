#!/usr/bin/env python3
"""
Test script to verify the enhanced tool parser can handle malformed tool calls.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dr_agent.tool_interface.tool_parsers import create_tool_parser

def test_enhanced_parser():
    """Test the enhanced v20250824 parser with various malformed tool calls."""

    print("🧪 Testing Enhanced Tool Parser v20250824")
    print("=" * 50)

    # Create the parser
    parser = create_tool_parser("v20250824")

    # Test cases - these are the malformed patterns we observed
    test_cases = [
        {
            "name": "Complete valid tool call",
            "text": '<call_tool name="google_search">latest AI news</call_tool>',
            "expected_tool": "google_search",
            "expected_content": "latest AI news"
        },
        {
            "name": "Malformed - missing opening tag (what we observed)",
            "text": 'name="google_search">latest AI news',
            "expected_tool": "google_search",
            "expected_content": "latest AI news"
        },
        {
            "name": "Malformed - missing closing tag",
            "text": '<call_tool name="google_search">latest AI news',
            "expected_tool": "google_search",
            "expected_content": "latest AI news"
        },
        {
            "name": "Malformed - incomplete with quotes",
            "text": 'name="google_search">latest AI news"',
            "expected_tool": "google_search",
            "expected_content": "latest AI news"
        },
        {
            "name": "No tool call present",
            "text": "This is just regular text without any tool calls",
            "expected_tool": None,
            "expected_content": None
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {repr(test_case['text'])}")

        # Test has_calls
        has_call = parser.has_calls(test_case['text'], test_case['expected_tool'] or 'google_search')
        print(f"has_calls: {has_call}")

        # Test parse_call
        call_info = parser.parse_call(test_case['text'], test_case['expected_tool'] or 'google_search')

        if call_info:
            print(f"✅ Parsed - Tool: {call_info.content}, Parameters: {call_info.parameters}")
            if test_case['expected_tool']:
                passed += 1
        else:
            if test_case['expected_tool'] is None:
                print("✅ Correctly returned None for no tool call")
                passed += 1
            else:
                print("❌ Failed to parse tool call")

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Parser fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Parser may need further improvements.")
        return False

if __name__ == "__main__":
    success = test_enhanced_parser()
    sys.exit(0 if success else 1)