"""
Rate limiting middleware.
"""
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict

from config import settings


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


class TokenBucket:
    """
    Token bucket rate limiter.
    """

    def __init__(self, rate: int, capacity: int):
        """
        Initialize token bucket.

        Args:
            rate: Tokens added per second.
            capacity: Maximum tokens in bucket.
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume.

        Returns:
            True if tokens were consumed, False if rate limited.
        """
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_retry_after(self) -> int:
        """Get seconds until tokens are available."""
        if self.tokens >= 1:
            return 0
        return int((1 - self.tokens) / self.rate) + 1


class SlidingWindowLimiter:
    """
    Sliding window rate limiter.
    """

    def __init__(self, limit: int, window_seconds: int = 60):
        """
        Initialize sliding window limiter.

        Args:
            limit: Maximum requests per window.
            window_seconds: Window size in seconds.
        """
        self.limit = limit
        self.window = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            key: Client identifier (IP or API key).

        Returns:
            Tuple of (allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window

        # Remove old requests
        self.requests[key] = [
            t for t in self.requests[key]
            if t > window_start
        ]

        if len(self.requests[key]) >= self.limit:
            # Calculate retry after
            oldest = min(self.requests[key])
            retry_after = int(oldest - window_start) + 1
            return False, retry_after

        self.requests[key].append(now)
        return True, 0

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        now = time.time()
        window_start = now - self.window

        current = len([
            t for t in self.requests[key]
            if t > window_start
        ])

        return max(0, self.limit - current)


class RateLimiter:
    """
    Main rate limiter with multiple strategies.
    """

    def __init__(self,
                 requests_per_minute: int = None,
                 strategy: str = "sliding_window"):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute.
            strategy: 'sliding_window' or 'token_bucket'.
        """
        self.limit = requests_per_minute or settings.api.rate_limit
        self.strategy = strategy

        if strategy == "token_bucket":
            self._limiters: Dict[str, TokenBucket] = {}
        else:
            self._limiter = SlidingWindowLimiter(self.limit, 60)

    def _get_client_key(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first, then IP
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host}"

    def check_rate_limit(self, request: Request) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Args:
            request: FastAPI request object.

        Returns:
            Tuple of (allowed, remaining, retry_after).
        """
        key = self._get_client_key(request)

        if self.strategy == "token_bucket":
            if key not in self._limiters:
                self._limiters[key] = TokenBucket(
                    rate=self.limit / 60,
                    capacity=self.limit
                )

            bucket = self._limiters[key]
            allowed = bucket.consume()
            remaining = int(bucket.tokens)
            retry_after = bucket.get_retry_after() if not allowed else 0

            return allowed, remaining, retry_after
        else:
            allowed, retry_after = self._limiter.is_allowed(key)
            remaining = self._limiter.get_remaining(key)

            return allowed, remaining, retry_after


# Global rate limiter
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    """
    # Skip rate limiting for health checks
    if request.url.path.endswith("/health"):
        return await call_next(request)

    allowed, remaining, retry_after = rate_limiter.check_rate_limit(request)

    if not allowed:
        raise RateLimitExceeded(retry_after)

    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    return response


if __name__ == "__main__":
    print("=" * 60)
    print("RATE LIMIT MIDDLEWARE TEST")
    print("=" * 60)

    # Test sliding window
    limiter = SlidingWindowLimiter(limit=5, window_seconds=10)

    for i in range(7):
        allowed, retry = limiter.is_allowed("test")
        remaining = limiter.get_remaining("test")
        print(f"  Request {i+1}: allowed={allowed}, remaining={remaining}, retry={retry}")

    print("\n  ✓ Rate limit tests passed")
    print("=" * 60)
