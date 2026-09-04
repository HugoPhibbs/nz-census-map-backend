import io
import subprocess
import argparse
import psycopg_pool
import functools
import pandas as pd
import psycopg
from psycopg.types.numeric import NumericLoader, NumericBinaryLoader

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

def start_db():
    subprocess.run(["docker", "compose", "up", "-d"], cwd="./scripts/db", check=True)

def stop_db(reset=False):
    down_cmd = ["docker", "compose", "down", "-v"] if reset else ["docker", "compose", "down"]
    subprocess.run(down_cmd, cwd="./scripts/db", check=True)
    
@functools.lru_cache(maxsize=1)
def get_db_connection_pool():
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericLoader)
    psycopg.adapters.register_loader("numeric", IntOrFloatNumericBinaryLoader)
    return psycopg_pool.ConnectionPool(conninfo="dbname=census-db user=admin password=devpassword host=localhost port=5432", min_size=1, max_size=10)

def fill_variables_table():
    all_variable_ids = pd.read_parquet("./data/db-tables/demographic_variables_table.parquet")
    
    pool = get_db_connection_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for row in all_variable_ids.itertuples(index=False):
                cur.execute(
                    """
                    INSERT INTO DEMOGRAPHIC_VARIABLES (variable_id, variable_unit, plain_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (row.variable_id, row.variable_unit, row.plain_name)
                )

def fill_areas_table():
    df = pd.read_parquet("./data/db-tables/areas_table.parquet")  # Ensure area_code is read as string to preserve leading zeros
    
    pool = get_db_connection_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for area in df.itertuples(index=False):
                cur.execute(
                    """
                    INSERT INTO AREAS (area_name, area_code, census_year, area_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (area.area_name, area.area_code, area.census_year, area.area_type)
                )
    

def fill_demographic_data_table():
    df = pd.read_parquet("./data/db-tables/demographic_data_table.parquet")

    pool = get_db_connection_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TEMP TABLE demographic_data_staging (
                    area_code TEXT,
                    census_year INT,
                    variable_id TEXT,
                    variable_value DOUBLE PRECISION
                ) ON COMMIT DROP
            """)

            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False)
            buf.seek(0)

            with cur.copy(
                "COPY demographic_data_staging (area_code, census_year, variable_id, variable_value) FROM STDIN WITH (FORMAT csv)"
            ) as copy:
                copy.write(buf.read())

            cur.execute("""
                INSERT INTO DEMOGRAPHIC_DATA (area_code, census_year, variable_id, variable_value)
                SELECT area_code, census_year, variable_id, variable_value
                FROM demographic_data_staging
                ON CONFLICT DO NOTHING
            """)

        conn.commit()
    
def fill_tables():
    fill_variables_table()
    fill_areas_table()
    fill_demographic_data_table()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database using Docker Compose.")
    parser.add_argument("--start", default=False, action="store_true", help="Create the database using Docker Compose.")
    parser.add_argument("--stop", default=False, action="store_true", help="Drop the database using Docker Compose.")
    parser.add_argument("--fill", default=False, action="store_true", help="Fill the database tables with data.")
    parser.add_argument("--reset", "-rv", default=False, action="store_true", help="Reset the database by stopping, starting, and filling it.")
    
    args = parser.parse_args()
    
    if args.stop or args.reset:
        stop_db(args.reset)
    elif args.start:
        start_db()
    elif args.fill:
        fill_tables()
    else:
        print("No action specified. Use --start, --stop, --fill, or --reset-vols.")
        
__all__ = ["get_db_connection_pool"]