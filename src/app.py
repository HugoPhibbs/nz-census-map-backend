import os
import time

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS
import psycopg

from src import query_engine
from src.utils import get_db_connection_pool

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

@app.route("/health")
def health_check():
    healthy = True
    try:
        start = time.perf_counter()
        with get_db_connection_pool().connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                db_ping_time = round((time.perf_counter() - start) * 1000, 2)
    except Exception as e:
        print(f"Database connection error: {e}")
        healthy = False
            
    if healthy and result and result[0] == 1:
        return {"status": "ok", "db_ping_time_ms": db_ping_time}, 200
    else:
        return {"status": "broken"}, 503


@app.route("/area")
@cache.cached(query_string=True)
def get_area_info():
    census_year = request.args.get("census_year")
    area_code = request.args.get("area_code")
    result = query_engine.area_info(census_year, area_code)

    if not result:
        return {"error": "Area not found"}, 404

    return result, 200


@app.route("/stats/area")
@cache.cached(query_string=True)
def get_area_stats():
    census_year = request.args.get("census_year")
    area_code = request.args.get("area_code")

    result = query_engine.area_stats(census_year, area_code)

    if not result:
        return {
            "error": "No statistics found for the specified area and census year"
        }, 404

    return result, 200


@app.route("/stats/variable/avgs")
@cache.cached(timeout=3600)
def get_variable_avgs():
    census_year = request.args.get("census_year", 2023)

    result = query_engine.variable_averages(census_year)
    return result, 200


@app.route("/stats/variable/ids/to-unit")
@cache.cached()
def get_variable_ids_to_unit():
    result = query_engine.variable_ids_to_unit()
    return result, 200


@app.route("/stats/variable/ids/to-name")
@cache.cached()
def get_variable_ids_to_name():
    result = query_engine.variable_ids_to_name()
    return result, 200


@app.route("/stats/variable/ids")
@cache.cached()
def get_all_variables():
    result = query_engine.all_variable_ids()
    return result, 200


@app.route("/stats/variable/<variable_id>/<census_year>")
@cache.cached(query_string=True)
def get_all_variable_stats(variable_id, census_year):

    result = query_engine.map_stats(variable_id, census_year)

    return result, 200

if __name__ == "__main__":
    print("Running a production server at http://localhost:5000")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)
