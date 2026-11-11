import uuid
from contextlib import contextmanager
from functools import lru_cache

from django.conf import settings
from redis import Redis, RedisError

from .providers import CollectionError, ProviderPolicy


_ACQUIRE = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) + tonumber(clock[2]) / 1000000
local duration = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local spacing = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('ZCARD', KEYS[1]) >= limit then return 0 end
if spacing > 0 and tonumber(redis.call('GET', KEYS[2]) or '0') > now then return 0 end
redis.call('ZADD', KEYS[1], now + duration, ARGV[4])
redis.call('EXPIRE', KEYS[1], math.ceil(duration + 1))
if spacing > 0 then
  redis.call('SET', KEYS[2], now + spacing, 'EX', math.ceil(spacing + duration + 1))
end
return 1
"""


_RELEASE = """return redis.call('ZREM', KEYS[1], ARGV[1])"""


@lru_cache(maxsize=8)
def _redis_client(url: str) -> Redis:
    return Redis.from_url(url, socket_connect_timeout=3, socket_timeout=3)


@contextmanager
def provider_slot(name: str, policy: ProviderPolicy):
    """Redis coordinates provider-wide limits across all workers."""
    policy.validate()
    token = str(uuid.uuid4())
    slots_key = f"stalker:kaggle:provider:{name}:slots"
    interval_key = f"stalker:kaggle:provider:{name}:next"
    client = _redis_client(settings.CELERY_BROKER_URL)
    try:
        slot_seconds = max(settings.CELERY_TASK_TIME_LIMIT, policy.request_timeout_seconds) + 30
        acquired = client.eval(
            _ACQUIRE, 2, slots_key, interval_key, slot_seconds,
            policy.max_concurrency, policy.min_interval_seconds, token,
        )
    except RedisError as exc:
        raise CollectionError("coordination_unavailable", retryable=True) from exc
    if not acquired:
        raise CollectionError("provider_capacity", retryable=True)
    try:
        yield
    finally:
        try:
            client.eval(_RELEASE, 1, slots_key, token)
        except RedisError:
            pass  # The slot has a bounded expiry and cannot remain held indefinitely.
