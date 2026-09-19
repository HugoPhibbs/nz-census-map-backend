import functools
import os

import psycopg
import psycopg_pool
from dotenv import load_dotenv
from psycopg.types.numeric import NumericBinaryLoader, NumericLoader

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


@functools.lru_cache(maxsize=1)
def get_db_connection_pool(use_dev=None):
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericLoader)
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericBinaryLoader)
    
    if use_dev is None:
        use_dev = os.getenv('USE_DEV_DB', 'false').lower() == 'true'
    
    if use_dev:
        conn_info = f"dbname={os.getenv('DB_NAME_DEV')} user={os.getenv('DB_USER_DEV')} password={os.getenv('DB_PASSWORD_DEV')} host={os.getenv('DB_HOST_DEV')} port={os.getenv('DB_PORT_DEV')}"
    else:
        conn_info = os.getenv('DB_CONNECTION_STRING_PROD')
        
        
        
    return psycopg_pool.ConnectionPool(conninfo=conn_info, min_size=1, max_size=10)

