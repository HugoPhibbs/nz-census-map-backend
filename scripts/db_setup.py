import subprocess
import argparse

def start_db():
    subprocess.run("docker compose up -d", cwd="./db", shell=True, check=True)

def stop_db():
    subprocess.run("docker compose down", cwd="./db", shell=True, check=True)
    
def fill_variables_table():
    pass

def fill_areas_table():
    pass

def fill_demographic_data_table():
    pass
    
def fill_tables():
    fill_variables_table()
    fill_areas_table()
    fill_demographic_data_table()
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the database using Docker Compose.")
    parser.add_argument("--start", action="store_true", help="Create the database using Docker Compose.")
    parser.add_argument("--stop", action="store_true", help="Drop the database using Docker Compose.")
    parser.add_argument("--fill", action="store_true", help="Fill the database tables with data.")
    
    args = parser.parse_args()
    
    if args.start:
        start_db()
    elif args.stop:
        stop_db()
    elif args.fill:
        fill_tables()