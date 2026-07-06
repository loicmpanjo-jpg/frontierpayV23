"""Async Redis event producer."""

import json

import redis.asyncio as redis

from config.config import get_settings
from event_bus.event_schema import BaseEvent

settings = get_settings()


class EventProducer:
    def __init__(self):
        self._redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_pool_size,
                decode_responses=True,
            )
        return self._redis

    async def publish(self, event: BaseEvent, channel: str = "afm:events") -> bool:
        redis_client = await self._get_redis()
        message = json.dumps(event.model_dump(mode="json"), default=str)
        result = await redis_client.publish(channel, message)
        return result > 0

    async def close(self):
        if self._redis:
            await self._redis.close()


event_producer = EventProducer()
