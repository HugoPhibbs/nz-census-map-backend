import functools
import os

import gzip
import brotli
from compression import zstd

from flask import Response, make_response, request
import redis

from src.utils import get_redis_connection_pool


redis_client = redis.Redis(connection_pool=get_redis_connection_pool())
CACHE_PREFIX = os.getenv("K_REVISION", "local")  # K_REVISION is set by GCP in Cloud Run
CACHE_TIMEOUT = 60 * 60  # 1 hour

ENCODERS = {
    "zstd": lambda data: zstd.compress(data, level=3),
    "br": lambda data: brotli.compress(data, quality=4),
    "gzip": lambda data: gzip.compress(data, compresslevel=6),
}


def cached_response(
    compress: bool = False, timeout: int = CACHE_TIMEOUT, query_string: bool = False
):
    """
    Caches the response of a Flask view function in Redis.

    :param compress: Whether to compress the response
    :param timeout: The time in seconds for which the cached response will be valid.
    :param query_string: If True, the query string will be included in the cache key.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            if compress:
                encoding = request.accept_encodings.best_match(list(ENCODERS))
                if encoding is None:
                    return view(*args, **kwargs)
            else:
                encoding = "identity"

            key = f"{CACHE_PREFIX}:response:{encoding}:{request.full_path if query_string else request.path}"

            try:
                cached = redis_client.get(key)
            except redis.RedisError:
                # Ignore cache errors
                cached = None

            if cached is not None:
                status_code, body = int(cached[:3]), cached[3:]
                return cached_response_obj(body, status_code, encoding, hit=True)

            response = make_response(view(*args, **kwargs))
            if response.status_code >= 400:  # Don't cache server or client errors
                return response

            body = response.get_data()

            if compress:
                body = ENCODERS[encoding](body)

            try:
                redis_client.set(
                    key, str(response.status_code).encode() + body, ex=timeout
                )
            except redis.RedisError:
                # Ignore cache errors
                pass

            return cached_response_obj(body, response.status_code, encoding, hit=False)

        return wrapper

    return decorator


def cached_response_obj(body, status, encoding, hit):
    response = Response(body, status=status, mimetype="application/json")
    if encoding != "identity":
        response.headers["Content-Encoding"] = encoding
    response.headers["Vary"] = "Accept-Encoding"
    response.headers["X-Cache"] = "HIT" if hit else "MISS"
    return response
