"""
Redis caching service for OCR results.
"""
import json
import hashlib
import time
from typing import Optional, Any
from dataclasses import dataclass

from config import settings


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    created_at: float
    expires_at: float
    hit_count: int = 0


class CacheService:
    """
    Caching service with Redis or in-memory fallback.
    """

    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL.
            default_ttl: Default TTL in seconds.
        """
        self.redis_url = redis_url or settings.cache.redis_url
        self.default_ttl = default_ttl
        self._redis = None
        self._memory_cache: dict = {}
        self._use_redis = settings.cache.enable_cache

        if self._use_redis:
            self._connect_redis()

    def _connect_redis(self):
        """Connect to Redis server."""
        try:
            import redis
            self._redis = redis.from_url(self.redis_url)
            self._redis.ping()
            print(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            print(f"Redis connection failed: {e}. Using memory cache.")
            self._redis = None
            self._use_redis = False

    def _generate_key(self, file_content: bytes, params: dict = None) -> str:
        """
        Generate cache key from file content and parameters.

        Args:
            file_content: File binary content.
            params: Processing parameters.

        Returns:
            Cache key string.
        """
        hasher = hashlib.sha256()
        hasher.update(file_content)

        if params:
            param_str = json.dumps(params, sort_keys=True)
            hasher.update(param_str.encode())

        return f"ocr:{hasher.hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                print(f"Redis get error: {e}")
        else:
            entry = self._memory_cache.get(key)
            if entry:
                if time.time() < entry.expires_at:
                    entry.hit_count += 1
                    return entry.data
                else:
                    del self._memory_cache[key]

        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.

        Returns:
            True if successful.
        """
        ttl = ttl or self.default_ttl

        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                print(f"Redis set error: {e}")
                return False
        else:
            now = time.time()
            self._memory_cache[key] = CacheEntry(
                data=value,
                created_at=now,
                expires_at=now + ttl
            )
            return True

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted.
        """
        if self._redis:
            try:
                return bool(self._redis.delete(key))
            except Exception:
                return False
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if self._redis:
            try:
                return bool(self._redis.exists(key))
            except Exception:
                return False
        else:
            entry = self._memory_cache.get(key)
            if entry and time.time() < entry.expires_at:
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cached values.

        Returns:
            Number of keys deleted.
        """
        if self._redis:
            try:
                keys = self._redis.keys("ocr:*")
                if keys:
                    return self._redis.delete(*keys)
            except Exception:
                pass
            return 0
        else:
            count = len(self._memory_cache)
            self._memory_cache.clear()
            return count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        if self._redis:
            try:
                info = self._redis.info()
                return {
                    "type": "redis",
                    "connected": True,
                    "keys": self._redis.dbsize(),
                    "memory_used": info.get("used_memory_human", "unknown")
                }
            except Exception:
                return {"type": "redis", "connected": False}
        else:
            total_hits = sum(e.hit_count for e in self._memory_cache.values())
            return {
                "type": "memory",
                "keys": len(self._memory_cache),
                "total_hits": total_hits
            }

    def cache_ocr_result(self, file_content: bytes, params: dict, result: dict) -> str:
        """
        Cache an OCR result.

        Args:
            file_content: Original file content.
            params: Processing parameters.
            result: OCR result to cache.

        Returns:
            Cache key.
        """
        key = self._generate_key(file_content, params)
        self.set(key, result)
        return key

    def get_ocr_result(self, file_content: bytes, params: dict) -> Optional[dict]:
        """
        Get cached OCR result.

        Args:
            file_content: Original file content.
            params: Processing parameters.

        Returns:
            Cached result or None.
        """
        key = self._generate_key(file_content, params)
        return self.get(key)


# Global cache service
cache_service = CacheService()


if __name__ == "__main__":
    print("=" * 60)
    print("CACHE SERVICE TEST")
    print("=" * 60)

    cache = CacheService()

    # Test set/get
    cache.set("test_key", {"data": "test_value"})
    result = cache.get("test_key")
    print(f"  Set/Get: {result}")

    # Test exists
    exists = cache.exists("test_key")
    print(f"  Exists: {exists}")

    # Test delete
    deleted = cache.delete("test_key")
    print(f"  Deleted: {deleted}")

    # Test stats
    stats = cache.get_stats()
    print(f"  Stats: {stats}")

    print("\n  ✓ Cache service tests passed")
    print("=" * 60)
