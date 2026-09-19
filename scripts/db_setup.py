import argparse
import io
import subprocess

import pandas as pd

from src.utils import get_db_connection_pool


def start_dev_db():
    subprocess.run(["docker", "compose", "up", "-d"], cwd="./scripts/db", check=True)

def stop_dev_db(reset=False):
    down_cmd = ["docker", "compose", "down", "-v"] if reset else ["docker", "compose", "down"]
    subprocess.run(down_cmd, cwd="./scripts/db", check=True)
    
def fill_variables_table(pool):
    all_variable_ids = pd.read_parquet("./data/db-tables/demographic_variables_table.parquet")
    
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

def fill_areas_table(pool):
    df = pd.read_parquet("./data/db-tables/areas_table.parquet")  # Ensure area_code is read as string to preserve leading zeros
    
    with pool.connection() as conn, conn.cursor() as cur:
        for area in df.itertuples(index=False):
            cur.execute(
                """
                    INSERT INTO AREAS (area_name, area_code, census_year, area_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                (area.area_name, area.area_code, area.census_year, area.area_type)
            )
    

def fill_demographic_data_table(pool):
    df = pd.read_parquet("./data/db-tables/demographic_data_table.parquet")

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
    
def fill_tables(pool=get_db_connection_pool()):
    fill_variables_table(pool)
    fill_areas_table(pool)
    fill_demographic_data_table(pool)

def create_tables_prod():
    pool = get_db_connection_pool(use_dev=False)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            with open("./scripts/db/create_tables.sql", "r") as f:
                cur.execute(f.read())
        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database using Docker Compose.")
    
    parser.add_argument("--start-dev", default=False, action="store_true", help="Create the database using Docker Compose.")
    parser.add_argument("--stop-dev", default=False, action="store_true", help="Drop the database using Docker Compose.")
    parser.add_argument("--reset-dev", "-rv", default=False, action="store_true", help="Reset the database by stopping, starting, and filling it.")
    parser.add_argument("--fill-dev", default=False, action="store_true", help="Fill the database tables with data.")
    
    parser.add_argument("--init-prod", default=False, action="store_true", help="Create the production database tables.")
    parser.add_argument("--fill-prod", default=False, action="store_true", help="Fill the database tables with data.")
    
    args = parser.parse_args()
    
    if args.stop_dev or args.reset_dev:
        stop_dev_db(args.reset_dev)
    elif args.start_dev:
        start_dev_db()
    elif args.init_prod:
        create_tables_prod()
    elif args.fill_dev:
        fill_tables(get_db_connection_pool(use_dev=True))
    elif args.fill_prod:
        fill_tables(get_db_connection_pool(use_dev=False))
    else:
        print("No action specified. Use --start, --stop, --fill, or --reset-vols.")
        