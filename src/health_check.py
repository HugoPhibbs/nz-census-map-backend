import time

import redis

from src.query_engine import run_query
from src.utils import get_redis_connection_pool


def duration_since_start_ms(start_time):
    return round((time.perf_counter() - start_time) * 1000, 2)

def db_health_check():
    try:
        start = time.perf_counter()
        run_query("SELECT 1", fetch_one=True)
        return duration_since_start_ms(start)
        
    except Exception as e:
        print(f"Database connection error: {e}")


def redis_health_check():
    try:
        redis_pool = get_redis_connection_pool()
        start = time.perf_counter()
        redis.Redis(connection_pool=redis_pool).ping()
        return duration_since_start_ms(start)
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None


def health_check():
    db_ping_time = db_health_check()
    redis_ping_time = redis_health_check()

    healthy = db_ping_time is not None and redis_ping_time is not None

    return healthy, db_ping_time, redis_ping_time