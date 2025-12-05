"""
Tool call caching system to avoid repeated API calls and research.
Stores tool call results with timestamps for intelligent caching.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import os


@dataclass
class CacheEntry:
    """Represents a cached tool call result"""
    tool_name: str
    query: str
    result: Any
    timestamp: float
    expiry_hours: float = 24.0  # Default expiry: 24 hours

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > (self.timestamp + (self.expiry_hours * 3600))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(**data)


class ToolCallCache:
    """Caches tool call results to avoid repeated expensive operations"""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".dr_tulu_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Separate cache files for different tool types
        self.search_cache_file = self.cache_dir / "search_cache.json"
        self.browse_cache_file = self.cache_dir / "browse_cache.json"
        self.facts_cache_file = self.cache_dir / "facts_cache.json"

        # In-memory caches for faster access
        self._search_cache: Dict[str, CacheEntry] = {}
        self._browse_cache: Dict[str, CacheEntry] = {}
        self._facts_cache: Dict[str, Dict[str, Any]] = {}

        # Load existing caches
        self._load_caches()

    def _get_cache_key(self, tool_name: str, query: str) -> str:
        """Generate a cache key for a tool call"""
        content = f"{tool_name}:{query}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_caches(self):
        """Load existing cache files"""
        # Load search cache
        if self.search_cache_file.exists():
            try:
                with open(self.search_cache_file, 'r') as f:
                    data = json.load(f)
                    self._search_cache = {
                        key: CacheEntry.from_dict(entry)
                        for key, entry in data.items()
                    }
            except Exception as e:
                print(f"Warning: Failed to load search cache: {e}")

        # Load browse cache
        if self.browse_cache_file.exists():
            try:
                with open(self.browse_cache_file, 'r') as f:
                    data = json.load(f)
                    self._browse_cache = {
                        key: CacheEntry.from_dict(entry)
                        for key, entry in data.items()
                    }
            except Exception as e:
                print(f"Warning: Failed to load browse cache: {e}")

        # Load facts cache
        if self.facts_cache_file.exists():
            try:
                with open(self.facts_cache_file, 'r') as f:
                    self._facts_cache = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load facts cache: {e}")

    def _save_caches(self):
        """Save caches to disk"""
        try:
            # Save search cache
            search_data = {
                key: entry.to_dict()
                for key, entry in self._search_cache.items()
            }
            with open(self.search_cache_file, 'w') as f:
                json.dump(search_data, f, indent=2)

            # Save browse cache
            browse_data = {
                key: entry.to_dict()
                for key, entry in self._browse_cache.items()
            }
            with open(self.browse_cache_file, 'w') as f:
                json.dump(browse_data, f, indent=2)

            # Save facts cache
            with open(self.facts_cache_file, 'w') as f:
                json.dump(self._facts_cache, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to save caches: {e}")

    def get_search_result(self, tool_name: str, query: str) -> Optional[Any]:
        """Get cached search result"""
        cache_key = self._get_cache_key(tool_name, query)

        if cache_key in self._search_cache:
            entry = self._search_cache[cache_key]
            if not entry.is_expired:
                print(f"[CACHE HIT] Search result found for {tool_name}: {query[:50]}...")
                return entry.result
            else:
                # Remove expired entry
                del self._search_cache[cache_key]

        return None

    def cache_search_result(self, tool_name: str, query: str, result: Any, expiry_hours: float = 24.0):
        """Cache a search result"""
        cache_key = self._get_cache_key(tool_name, query)

        entry = CacheEntry(
            tool_name=tool_name,
            query=query,
            result=result,
            timestamp=time.time(),
            expiry_hours=expiry_hours
        )

        self._search_cache[cache_key] = entry
        print(f"[CACHE STORE] Caching search result for {tool_name}: {query[:50]}...")
        self._save_caches()

    def get_browse_result(self, url: str) -> Optional[Any]:
        """Get cached browse result"""
        cache_key = self._get_cache_key("browse", url)

        if cache_key in self._browse_cache:
            entry = self._browse_cache[cache_key]
            if not entry.is_expired:
                print(f"[CACHE HIT] Browse result found for URL: {url[:50]}...")
                return entry.result
            else:
                # Remove expired entry
                del self._browse_cache[cache_key]

        return None

    def cache_browse_result(self, url: str, result: Any, expiry_hours: float = 168.0):  # 1 week default for URLs
        """Cache a browse result"""
        cache_key = self._get_cache_key("browse", url)

        entry = CacheEntry(
            tool_name="browse",
            query=url,
            result=result,
            timestamp=time.time(),
            expiry_hours=expiry_hours
        )

        self._browse_cache[cache_key] = entry
        print(f"[CACHE STORE] Caching browse result for URL: {url[:50]}...")
        self._save_caches()

    def store_key_facts(self, category: str, facts: Dict[str, Any]):
        """Store key facts about a technology or service"""
        if category not in self._facts_cache:
            self._facts_cache[category] = {}

        # Update with new facts, preserving existing ones
        self._facts_cache[category].update(facts)
        self._facts_cache[category]["_last_updated"] = time.time()

        print(f"[CACHE STORE] Storing {len(facts)} key facts for {category}")
        self._save_caches()

    def get_key_facts(self, category: str) -> Optional[Dict[str, Any]]:
        """Get cached key facts about a technology or service"""
        if category in self._facts_cache:
            facts = self._facts_cache[category]
            # Check if facts are stale (older than 7 days)
            if "_last_updated" in facts:
                age_days = (time.time() - facts["_last_updated"]) / 86400
                if age_days > 7:
                    print(f"[CACHE STALE] Facts for {category} are {age_days:.1f} days old")
                    # Still return them, but note they're stale
                    return facts

            print(f"[CACHE HIT] Found {len(facts)} facts for {category}")
            return facts

        return None

    def clear_cache(self, cache_type: str = "all"):
        """Clear specified cache type"""
        if cache_type in ("all", "search"):
            self._search_cache.clear()
            if self.search_cache_file.exists():
                self.search_cache_file.unlink()

        if cache_type in ("all", "browse"):
            self._browse_cache.clear()
            if self.browse_cache_file.exists():
                self.browse_cache.unlink()

        if cache_type in ("all", "facts"):
            self._facts_cache.clear()
            if self.facts_cache_file.exists():
                self.facts_cache.unlink()

        print(f"[CACHE] Cleared {cache_type} cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "search_cache_size": len(self._search_cache),
            "browse_cache_size": len(self._browse_cache),
            "facts_categories": list(self._facts_cache.keys()),
            "cache_directory": str(self.cache_dir)
        }


# Global cache instance
_global_cache: Optional[ToolCallCache] = None


def get_tool_cache() -> ToolCallCache:
    """Get or create the global tool cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ToolCallCache()
    return _global_cache


def cache_cloud_pricing_facts():
    """Helper function to cache common cloud pricing facts"""
    cache = get_tool_cache()

    # Common pricing patterns and facts that don't change frequently
    common_facts = {
        "aws_regions": {
            "us-east-1": "N. Virginia",
            "us-west-2": "Oregon",
            "eu-west-1": "Ireland",
            "ap-southeast-1": "Singapore"
        },
        "instance_families": {
            "t3": "General purpose, burstable",
            "m5": "General purpose",
            "c5": "Compute optimized",
            "r5": "Memory optimized"
        },
        "pricing_models": {
            "on_demand": "Pay per hour without commitment",
            "reserved": "1-3 year commitment for discount",
            "spot": "Up to 90% discount, can be interrupted"
        }
    }

    cache.store_key_facts("aws_common", common_facts)


# Initialize common facts on import
try:
    cache_cloud_pricing_facts()
except Exception:
    pass  # Ignore errors during initialization