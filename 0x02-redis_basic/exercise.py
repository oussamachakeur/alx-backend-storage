#!/usr/bin/env python3
"""
This module provides a Cache class that interfaces with Redis for storing
and retrieving data, tracking method calls, and logging call history.
"""
import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator to count how many times a method is called.
    Stores the count in Redis under the method's qualified name.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator to store the history of inputs and outputs for a method.
    Inputs stored at <method_name>:inputs, outputs at <method_name>:outputs
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"
        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


def replay(method: Callable) -> None:
    """
    Display the history of calls of a particular function.
    Prints inputs and corresponding outputs.
    """
    r = method.__self__._redis
    name = method.__qualname__
    inputs = r.lrange(f"{name}:inputs", 0, -1)
    outputs = r.lrange(f"{name}:outputs", 0, -1)
    print(f"{name} was called {len(inputs)} times:")
    for i, o in zip(inputs, outputs):
        print(f"{name}(*{i.decode('utf-8')}) -> {o.decode('utf-8')}")


class Cache:
    """
    Cache class to interact with Redis.
    Provides methods for storing and retrieving data, and decorators
    for call tracking and history.
    """

    def __init__(self):
        """Initialize Redis connection and flush database."""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Store data in Redis with a random key and return the key."""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis and optionally convert it using fn.
        If key doesn't exist, return None.
        """
        val = self._redis.get(key)
        if val is None:
            return None
        if fn:
            return fn(val)
        return val

    def get_str(self, key: str) -> str:
        """Retrieve string value from Redis by decoding bytes to UTF-8."""
        return self.get(key, lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> int:
        """Retrieve integer value from Redis by converting bytes to int."""
        return self.get(key, lambda d: int(d))
