"""Small process target for Redis integration tests; imports no Django models."""

from redis import Redis


def acquire_in_process(args):
    url, script, slots, spacing, token = args
    return Redis.from_url(url).eval(script, 2, slots, spacing, 5, 1, 0, token)
