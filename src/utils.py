import functools
import os

import psycopg
import psycopg_pool
from dotenv import load_dotenv
from psycopg.types.numeric import NumericBinaryLoader, NumericLoader
import redis

load_dotenv()

# The below code handles converting NUMERIC to float or int.
# See https://www.psycopg.org/docs/usage.html#numbers-adaptation


def normalize_numeric(value):
    return int(value) if value == value.to_integral_value() else float(value)


class IntOrFloatNumericLoader(NumericLoader):
    def load(self, data):
        return normalize_numeric(super().load(data))


class IntOrFloatNumericBinaryLoader(NumericBinaryLoader):
    def load(self, data):
        return normalize_numeric(super().load(data))

@functools.lru_cache
def get_db_connection_pool(autocommit=False):
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericLoader)
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericBinaryLoader)

    conninfo = psycopg.conninfo.make_conninfo(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"]
    )

    return psycopg_pool.ConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=10,
        kwargs={"autocommit": autocommit},
    )

@functools.lru_cache
def get_redis_connection_pool():
    if not (redis_url := os.getenv("REDIS_URL")):
        raise ValueError("REDIS_URL environment variable is not set.")
    try:
        return redis.ConnectionPool.from_url(
            redis_url, 
            max_connections = 10,
            socket_connect_timeout = 3,
            socket_timeout = 3,
            health_check_interval = 30,
        )
        
    except Exception as e:
        print(f"Error creating Redis connection pool: {e}")
        raise