"""
Persistent fact cache using SQLite for long-term storage.
This module provides a simple interface to cache and retrieve facts
that persist over time with configurable TTL.
"""

import sqlite3
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class FactCache:
    """SQLite-based persistent fact cache with long-term storage."""

    def __init__(self, db_path: str = None, default_ttl_hours: int = 720):
        """
        Initialize fact cache with SQLite backend.

        Args:
            db_path: Path to SQLite database file (default: .beads/fact_cache.db)
            default_ttl_hours: Default TTL in hours (default: 720 = 30 days)
        """
        if db_path is None:
            # Default to .beads directory for persistence
            beads_dir = os.path.join(os.getcwd(), '.beads')
            os.makedirs(beads_dir, exist_ok=True)
            db_path = os.path.join(beads_dir, 'fact_cache.db')

        self.db_path = db_path
        self.default_ttl = timedelta(hours=default_ttl_hours)

        # Initialize database
        self._init_db()
        logger.info(f"Initialized SQLite fact cache at {db_path}")

    def _init_db(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS facts (
                        key TEXT PRIMARY KEY,
                        value BLOB NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    )
                ''')

                # Create index for expiration queries
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_expires_at ON facts(expires_at)
                ''')

                conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _cleanup_expired(self):
        """Remove expired facts from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM facts WHERE expires_at < CURRENT_TIMESTAMP')
                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.debug(f"Cleaned up {deleted_count} expired facts")

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup expired facts: {e}")

    def set_fact(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
        """
        Store a fact with optional custom TTL.

        Args:
            key: Fact identifier
            value: Fact data (any serializable object)
            ttl_hours: Custom TTL in hours, uses default if None

        Returns:
            True if successfully stored, False otherwise
        """
        try:
            # Calculate expiration time
            ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
            expires_at = datetime.now() + ttl

            # Serialize the value
            serialized_value = pickle.dumps(value)

            # Store in SQLite
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO facts (key, value, expires_at)
                    VALUES (?, ?, ?)
                ''', (key, serialized_value, expires_at))
                conn.commit()

            logger.info(f"Stored fact: {key} (expires: {expires_at})")
            return True

        except Exception as e:
            logger.error(f"Failed to store fact {key}: {e}")
            return False

    def get_fact(self, key: str) -> Optional[Any]:
        """
        Retrieve a fact from cache.

        Args:
            key: Fact identifier

        Returns:
            Fact data if found and not expired, None otherwise
        """
        try:
            # First cleanup any expired facts
            self._cleanup_expired()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT value FROM facts
                    WHERE key = ? AND expires_at > CURRENT_TIMESTAMP
                ''', (key,))

                row = cursor.fetchone()

                if row:
                    value = pickle.loads(row[0])
                    logger.debug(f"Retrieved fact: {key}")
                    return value
                else:
                    logger.debug(f"Fact not found or expired: {key}")
                    return None

        except Exception as e:
            logger.error(f"Failed to retrieve fact {key}: {e}")
            return None

    def delete_fact(self, key: str) -> bool:
        """
        Delete a fact from cache.

        Args:
            key: Fact identifier

        Returns:
            True if deleted, False if not found or error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM facts WHERE key = ?', (key,))
                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Deleted fact: {key}")
                    return True
                else:
                    logger.debug(f"Fact not found for deletion: {key}")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete fact {key}: {e}")
            return False

    def list_facts(self, pattern: str = "%") -> List[str]:
        """
        List all fact keys matching pattern.

        Args:
            pattern: SQL LIKE pattern for matching keys (default: "%")

        Returns:
            List of fact keys
        """
        try:
            # Cleanup expired facts first
            self._cleanup_expired()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key FROM facts
                    WHERE key LIKE ? AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY key
                ''', (pattern,))

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to list facts: {e}")
            return []

    def get_fact_metadata(self, key: str) -> Optional[Dict]:
        """
        Get metadata about a stored fact.

        Args:
            key: Fact identifier

        Returns:
            Dictionary with metadata or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT created_at, expires_at,
                           CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 ELSE 0 END as is_valid
                    FROM facts WHERE key = ?
                ''', (key,))

                row = cursor.fetchone()
                if row:
                    created_at, expires_at, is_valid = row
                    return {
                        'key': key,
                        'created_at': created_at,
                        'expires_at': expires_at,
                        'is_valid': bool(is_valid),
                        'ttl_seconds': (expires_at - datetime.now()).total_seconds() if is_valid else 0
                    }
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to get metadata for fact {key}: {e}")
            return None

    def clear_all_facts(self) -> bool:
        """
        Clear all facts from cache. Use with caution!

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM facts')
                count_before = cursor.fetchone()[0]

                cursor.execute('DELETE FROM facts')
                conn.commit()

                logger.warning(f"Cleared {count_before} facts from cache")
            return True

        except Exception as e:
            logger.error(f"Failed to clear facts: {e}")
            return False

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            # Cleanup expired facts first
            self._cleanup_expired()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total facts
                cursor.execute('SELECT COUNT(*) FROM facts WHERE expires_at > CURRENT_TIMESTAMP')
                total_facts = cursor.fetchone()[0]

                # Database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                # Oldest and newest fact
                cursor.execute('''
                    SELECT MIN(created_at), MAX(created_at)
                    FROM facts WHERE expires_at > CURRENT_TIMESTAMP
                ''')
                oldest, newest = cursor.fetchone()

                return {
                    'total_facts': total_facts,
                    'database_size_bytes': db_size,
                    'oldest_fact': oldest,
                    'newest_fact': newest,
                    'database_path': self.db_path
                }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    def vacuum(self):
        """Optimize the SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('VACUUM')
                logger.info("Database vacuumed successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {e}")


# Global instance for easy access
fact_cache = FactCache()

# Convenience functions
def cache_fact(key: str, value: Any, ttl_hours: Optional[int] = None) -> bool:
    """Cache a fact using the global instance."""
    return fact_cache.set_fact(key, value, ttl_hours)

def get_cached_fact(key: str) -> Optional[Any]:
    """Retrieve a cached fact using the global instance."""
    return fact_cache.get_fact(key)

def delete_cached_fact(key: str) -> bool:
    """Delete a cached fact using the global instance."""
    return fact_cache.delete_fact(key)