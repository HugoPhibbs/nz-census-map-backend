import subprocess
import argparse
import json
import psycopg_pool
import functools
import pandas as pd

def start_db():
    subprocess.run(["docker", "compose", "up", "-d"], cwd="./scripts/db", check=True)

def stop_db(reset_vols=False):
    down_cmd = ["docker", "compose", "down", "-v"] if reset_vols else ["docker", "compose", "down"]
    subprocess.run(down_cmd, cwd="./scripts/db", check=True)
    
@functools.lru_cache(maxsize=1)
def get_db_connection_pool():
    return psycopg_pool.ConnectionPool(conninfo="dbname=census-db user=admin password=devpassword host=localhost port=5432", min_size=1, max_size=10)

def fill_variables_table():
    all_variable_names = pd.read_csv("./data/all_variable_names.csv", header=None)[0]
    
    pool = get_db_connection_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for variable_name in all_variable_names:
                cur.execute(
                    """
                    INSERT INTO DEMOGRAPHIC_VARIABLES (variable_name, variable_unit)
                    VALUES (%s, NULL)
                    ON CONFLICT DO NOTHING
                    """,
                    (variable_name,)
                )
    
    pass

def fill_areas_table():
    with open("./data/all_area_properties.json", "r", encoding="utf-8") as f:
        all_areas = json.load(f)
        
    pool = get_db_connection_pool()
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for area in all_areas:
                cur.execute(
                    """
                    INSERT INTO AREAS (area_name, area_code, census_year, area_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (area["area_name"], area["area_code"], area["census_year"], area["area_type"])
                )
    

def fill_demographic_data_table():
    pass
    
def fill_tables():
    fill_variables_table()
    fill_areas_table()
    fill_demographic_data_table()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database using Docker Compose.")
    parser.add_argument("--start", default=False, action="store_true", help="Create the database using Docker Compose.")
    parser.add_argument("--stop", default=False, action="store_true", help="Drop the database using Docker Compose.")
    parser.add_argument("--fill", default=False, action="store_true", help="Fill the database tables with data.")
    parser.add_argument("--reset-vols", "-rv", default=False, action="store_true", help="Reset the database by stopping, starting, and filling it.")
    
    args = parser.parse_args()
    
    if args.stop or args.reset_vols:
        stop_db(args.reset_vols)
    elif args.start:
        start_db()
    elif args.fill:
        fill_tables()
    else:
        print("No action specified. Use --start, --stop, --fill, or --reset-vols.")