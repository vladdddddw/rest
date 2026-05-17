import time
import uuid
from typing import Optional

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request

from core.dependencies import get_optional_user
from redis_client import get_redis_client

RATE_LIMITS = {
    "anonymous": (3, 60),         # 3 requests per 60 seconds
    "authenticated": (15, 60),    # 15 requests per 60 seconds
}


async def rate_limit(
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user),
    redis: aioredis.Redis = Depends(get_redis_client),
) -> None:
    uid = current_user["id"] if current_user else None
    identity = uid or request.client.host
    bucket = "authenticated" if uid else "anonymous"
    max_hits, window = RATE_LIMITS[bucket]

    key = f"rl:{identity}"
    ts = int(time.time())
    cutoff = ts - window

    await redis.zremrangebyscore(key, 0, cutoff)
    hits = await redis.zcard(key)

    if hits >= max_hits:
        retry_in = window - (ts - cutoff)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_in} seconds.",
            headers={"Retry-After": str(retry_in)},
        )

    await redis.zadd(key, {f"{ts}:{uuid.uuid4()}": ts})
    await redis.expire(key, window)
