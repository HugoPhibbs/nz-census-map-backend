import argparse
import io
import time

import pandas as pd

from src.utils import get_db_connection_pool
    
def fill_variables_table(pool):
    variables_df = pd.read_parquet("./data/db-tables/demographic_variables_table.parquet")
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for row in variables_df.itertuples(index=False):
                cur.execute(
                    """
                    INSERT INTO DEMOGRAPHIC_VARIABLES (variable_id, variable_unit, plain_name, available_years, description)
                    VALUES (%s, %s, %s, %s::integer[], %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (row.variable_id, row.variable_unit, row.plain_name, [int(y) for y in row.available_years], row.description)
                )

def fill_areas_table(pool):
    df = pd.read_parquet("./data/db-tables/areas_table.parquet")  # Ensure area_id is read as string to preserve leading zeros
    
    with pool.connection() as conn, conn.cursor() as cur:
        # executemany batches inserts, so its faster
        cur.executemany(
            """
            INSERT INTO AREAS (area_name, area_id, area_type, bounding_box)
            VALUES (%s, %s, %s, %s::float8[])
            ON CONFLICT DO NOTHING
            """,
            [
                (area.area_name, area.area_id, area.area_type, [float(x) for x in area.bounding_box])
                for area in df.itertuples(index=False)
            ],
        )
    

def fill_demographic_data_table(pool):
    demo_df = pd.read_parquet("./data/db-tables/demographic_data_table.parquet")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TEMP TABLE demographic_data_staging (
                    area_id TEXT,
                    census_year INT,
                    variable_id TEXT,
                    variable_value DOUBLE PRECISION
                ) ON COMMIT DROP
            """)

            buf = io.StringIO()
            demo_df.to_csv(buf, index=False, header=False)
            buf.seek(0)

            with cur.copy(
                "COPY demographic_data_staging (area_id, census_year, variable_id, variable_value) FROM STDIN WITH (FORMAT csv)"
            ) as copy:
                copy.write(buf.read())

            cur.execute("""
                INSERT INTO DEMOGRAPHIC_DATA (area_id, census_year, variable_id, variable_value)
                SELECT area_id, census_year, variable_id, variable_value
                FROM demographic_data_staging
                ON CONFLICT DO NOTHING
            """)

        conn.commit()

def refresh_materialized_views(pool):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW national_percentage_averages")
        conn.commit()
    
def fill_tables(pool):
    fill_variables_table(pool)
    fill_areas_table(pool)
    fill_demographic_data_table(pool)
    refresh_materialized_views(pool)

def create_tables_prod():
    pool = get_db_connection_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            with open("./scripts/db/create_tables.sql", "r") as f:
                cur.execute(f.read())
        conn.commit()

    return pool

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database using Docker Compose.")
    
    parser.add_argument("--init-prod", default=False, action="store_true", help="Create the production database tables.")
    parser.add_argument("--fill-prod", default=False, action="store_true", help="Fill the database tables with data.")
    
    args = parser.parse_args()
    
    if args.init_prod:
        pool = create_tables_prod()
    elif args.fill_prod:
        fill_tables(get_db_connection_pool())
    else:
        print("No action specified. Use --start, --stop, --fill, or --reset-vols.")