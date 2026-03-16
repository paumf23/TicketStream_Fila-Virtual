


import redis.asyncio as aioredis

from app.redis import redis_pool


def _queue_key(event_id: str) -> str:
    return f"queue:{event_id}"


def _allowed_key(event_id: str, user_id: str) -> str:
    return f"allowed:{event_id}:{user_id}"


def _channel_key(event_id: str) -> str:
    return f"channel:queue:{event_id}"


async def queue_push(event_id: str, user_id: str) -> int:
    position = await redis_pool.rpush(_queue_key(event_id), user_id)
    return position


async def queue_pop(event_id: str, batch_size: int = 10) -> list[str]:
    users = []
    for _ in range(batch_size):
        user_id = await redis_pool.lpop(_queue_key(event_id))
        if user_id is None:
            break
        users.append(user_id)
    return users


async def queue_position(event_id: str, user_id: str) -> int | None:
    pos = await redis_pool.lpos(_queue_key(event_id), user_id)
    return pos


async def queue_length(event_id: str) -> int:
    return await redis_pool.llen(_queue_key(event_id))


async def queue_remove(event_id: str, user_id: str) -> bool:
    removed = await redis_pool.lrem(_queue_key(event_id), 1, user_id)
    return removed > 0


async def set_allowed(event_id: str, user_id: str, ttl_seconds: int = 300) -> None:
    key = _allowed_key(event_id, user_id)
    await redis_pool.set(key, "1", ex=ttl_seconds)


async def is_allowed(event_id: str, user_id: str) -> bool:
    result = await redis_pool.get(_allowed_key(event_id, user_id))
    return result is not None


async def remove_allowed(event_id: str, user_id: str) -> None:
    await redis_pool.delete(_allowed_key(event_id, user_id))



async def publish(event_id: str, message: str) -> int:
    return await redis_pool.publish(_channel_key(event_id), message)


async def subscribe(event_id: str) -> aioredis.client.PubSub:

    pubsub = redis_pool.pubsub()
    await pubsub.subscribe(_channel_key(event_id))
    return pubsub


def _user_name_key(user_id: str) -> str:

    return f"user_name:{user_id}"


async def set_user_name(
    user_id: str, first_name: str, last_name: str
) -> None:

    key = _user_name_key(user_id)
    await redis_pool.hset(key, mapping={
        "first_name": first_name,
        "last_name": last_name,
    })
    await redis_pool.expire(key, 3600)


async def get_user_name(user_id: str) -> dict | None:

    key = _user_name_key(user_id)
    data = await redis_pool.hgetall(key)
    if not data:
        return None
    return {
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
    }

