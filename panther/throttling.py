from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from panther.db.connections import redis
from panther.exceptions import ThrottlingAPIError
from panther.request import Request
from panther.utils import round_datetime

# In-memory fallback storage for when Redis is unavailable
_fallback_throttle_storage = defaultdict(int)


@dataclass(repr=False, eq=False)
class Throttle:
    rate: int
    duration: timedelta

    @property
    def time_window(self) -> datetime:
        return round_datetime(datetime.now(), self.duration)

    def build_cache_key(self, request: Request) -> str:
        """
        Generate a unique cache key based on time window, user or IP, and path.
        This method is intended to be overridden by subclasses to customize throttling logic.
        """
        identifier = request.user.id if request.user else request.client.ip
        return f'{self.time_window}-{identifier}-{request.path}'

    async def get_request_count(self, request: Request) -> int:
        """
        Get the current request count for this key from Redis or fallback memory.
        """
        key = self.build_cache_key(request)

        if redis.is_connected:
            value = await redis.get(key)
            return int(value) if value else 0

        return _fallback_throttle_storage.get(key, 0)

    async def increment_request_count(self, request: Request) -> None:
        """
        Increment the request count for this key and ensure TTL is set in Redis.
        """
        key = self.build_cache_key(request)

        if redis.is_connected:
            count = await redis.incrby(key, amount=1)
            if count == 1:
                ttl = int(self.duration.total_seconds())
                await redis.expire(key, ttl)
        else:
            _fallback_throttle_storage[key] += 1

    async def check_and_increment(self, request: Request) -> None:
        """
        Main throttling logic:
        - Raises ThrottlingAPIError if limit exceeded.
        - Otherwise increments the request count.
        """
        count = await self.get_request_count(request)
        remaining = self.rate - count - 1
        reset_time = self.time_window + self.duration
        retry_after = int((reset_time - datetime.now()).total_seconds())

        if remaining < 0:
            raise ThrottlingAPIError(
                headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Reset': str(int(reset_time.timestamp())),
                },
            )

        await self.increment_request_count(request)
