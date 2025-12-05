"""
Cached wrapper for search and browse tools to avoid repeated API calls.
Integrates with the tool cache system.
"""

from typing import Any, Dict, List, Optional
from functools import wraps
import json

from dr_agent.utils.tool_cache import get_tool_cache


def cache_search_results(tool_name: str):
    """Decorator to cache search tool results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_tool_cache()

            # Extract query from args/kwargs - this depends on the tool signature
            if args:
                query = args[0] if isinstance(args[0], str) else str(args[0])
            else:
                # Try to get query from kwargs
                query = kwargs.get('query') or kwargs.get('q') or str(kwargs)

            # Check cache first
            cached_result = cache.get_search_result(tool_name, query)
            if cached_result is not None:
                return cached_result

            # Call the actual function
            result = func(*args, **kwargs)

            # Cache the result
            cache.cache_search_result(tool_name, query, result)

            return result

        return wrapper
    return decorator


def cache_browse_results(func):
    """Decorator to cache browse tool results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_tool_cache()

        # Extract URL from args/kwargs
        if args:
            url = args[0] if isinstance(args[0], str) else str(args[0])
        else:
            url = kwargs.get('url') or kwargs.get('uri') or str(kwargs)

        # Check cache first
        cached_result = cache.get_browse_result(url)
        if cached_result is not None:
            return cached_result

        # Call the actual function
        result = func(*args, **kwargs)

        # Cache the result
        cache.cache_browse_result(url, result)

        return result

    return wrapper


class CachedSearchTool:
    """Wrapper for search tools that provides caching"""

    def __init__(self, search_tool, tool_name: str):
        self.search_tool = search_tool
        self.tool_name = tool_name

    def __call__(self, query: str, **kwargs) -> Any:
        cache = get_tool_cache()

        # Check cache first
        cached_result = cache.get_search_result(self.tool_name, query)
        if cached_result is not None:
            return cached_result

        # Call the actual search tool
        result = self.search_tool(query, **kwargs)

        # Cache the result
        cache.cache_search_result(self.tool_name, query, result)

        return result


class CachedBrowseTool:
    """Wrapper for browse tools that provides caching"""

    def __init__(self, browse_tool):
        self.browse_tool = browse_tool

    def __call__(self, url: str, **kwargs) -> Any:
        cache = get_tool_cache()

        # Check cache first
        cached_result = cache.get_browse_result(url)
        if cached_result is not None:
            return cached_result

        # Call the actual browse tool
        result = self.browse_tool(url, **kwargs)

        # Cache the result
        cache.cache_browse_result(url, result)

        return result


def extract_and_cache_pricing_facts(response_text: str, technology: str):
    """Extract and cache key pricing facts from tool responses"""
    cache = get_tool_cache()

    # Simple extraction of pricing information
    # This could be enhanced with more sophisticated NLP
    facts = {}

    # Look for common pricing patterns
    import re

    # Extract dollar amounts
    price_patterns = [
        r'\$(\d+\.\d+)/hour',
        r'\$(\d+\.\d+)/month',
        r'\$(\d+)',
        r'(\d+\.\d+)\s*USD/hour',
        r'(\d+\.\d+)\s*USD/month'
    ]

    for pattern in price_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            facts['extracted_prices'] = matches
            break

    # Extract instance sizes mentioned
    instance_pattern = r'(t[23]\.micro|t[23]\.small|t[23]\.medium|m[45]\.large|r[45]\.large)'
    instances = re.findall(instance_pattern, response_text)
    if instances:
        facts['mentioned_instances'] = list(set(instances))

    # Extract regions
    region_pattern = r'(us-east-1|us-west-2|eu-west-1|ap-southeast-1)'
    regions = re.findall(region_pattern, response_text)
    if regions:
        facts['mentioned_regions'] = list(set(regions))

    # Store if we found anything useful
    if facts:
        category = f"{technology}_pricing_facts"
        cache.store_key_facts(category, facts)
        print(f"[CACHE] Extracted and cached {len(facts)} pricing facts for {technology}")


def get_cached_facts_for_technology(technology: str) -> Optional[Dict[str, Any]]:
    """Get cached facts about a specific technology"""
    cache = get_tool_cache()
    return cache.get_key_facts(f"{technology}_pricing_facts")