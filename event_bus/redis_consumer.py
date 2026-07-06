"""Async Redis consumer with consumer groups."""

import asyncio
import json

import redis.asyncio as redis

from config.config import get_settings

settings = get_settings()


class EventConsumer:
    def __init__(self, group_name: str = "afm_consumers", consumer_name: str | None = None):
        self.group_name = group_name
        self.consumer_name = consumer_name or "consumer_default"
        self._redis = None

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_pool_size,
                decode_responses=True,
            )
        return self._redis

    async def create_group(self, stream: str) -> None:
        redis_client = await self._get_redis()
        try:
            await redis_client.xgroup_create(stream, self.group_name, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "already exists" not in str(e):
                raise

    async def consume(self, stream: str, handler: callable, block_ms: int = 5000, count: int = 10):
        redis_client = await self._get_redis()
        await self.create_group(stream)

        while True:
            try:
                messages = await redis_client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={stream: ">"},
                    count=count,
                    block=block_ms,
                )

                for stream_name, entries in messages:
                    for msg_id, fields in entries:
                        try:
                            data = json.loads(fields.get("data", "{}"))
                            await handler(data)
                            await redis_client.xack(stream, self.group_name, msg_id)
                        except Exception as e:
                            print(f"Error processing message {msg_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Consumer error: {e}")
                await asyncio.sleep(1)

    async def close(self):
        if self._redis:
            await self._redis.close()
