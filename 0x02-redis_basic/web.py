#!/usr/bin/env python3
"""
This module provides a function to fetch web pages
with caching and request count tracking using Redis.
"""
import redis
import requests
from typing import Callable
from functools import wraps

r = redis.Redis()


def count_url_access(method: Callable) -> Callable:
    """
    Decorator to count how many times a specific URL is accessed.
    Increments count stored in Redis at key 'count:{url}'
    """
    @wraps(method)
    def wrapper(url: str) -> str:
        redis_key = f"count:{url}"
        r.incr(redis_key)
        return method(url)
    return wrapper


def cache_result(expire: int = 10) -> Callable:
    """
    Decorator to cache results of a function for a given key.
    Caches data in Redis with expiration.
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str) -> str:
            cached_data = r.get(url)
            if cached_data:
                return cached_data.decode('utf-8')
            result = method(url)
            r.setex(url, expire, result)
            return result
        return wrapper
    return decorator


@count_url_access
@cache_result(expire=10)
def get_page(url: str) -> str:
    """
    Fetches HTML content of the given URL, caches it in Redis,
    and tracks the number of accesses. Cached result expires in 10 seconds.
    """
    response = requests.get(url)
    return response.text
