import os
import time

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS

from src import query_engine
from src.utils import get_db_connection_pool

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])

app.config["COMPRESS_MIN_SIZE"] = 450
compress = Compress(app)

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

@app.route("/health")
def health_check():
    healthy = True
    try:
        with get_db_connection_pool().connection() as conn:
            with conn.cursor() as cur:
                start = time.perf_counter()
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


@app.route("/area/<area_id>")
@cache.cached()
def get_area_info(area_id):
    result = query_engine.area_info(area_id)

    if not result:
        return {"error": "Area not found"}, 404

    return result, 200


@app.route("/stats/area/<area_id>/<int:census_year>")
@cache.cached()
def get_area_stats(area_id, census_year):
    result = query_engine.area_stats(census_year, area_id)

    if not result:
        return {
            "error": "No statistics found for the specified area and census year"
        }, 404

    return result, 200



@app.route("/stats/variable/avgs/<int:census_year>")
@cache.cached(timeout=3600)
def get_variable_avgs(census_year):
    result = query_engine.variable_averages(census_year)
    
    if result == {}:
        return {
            "error": "No statistics found for the specified census year"
        }, 404
    
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

@app.route("/stats/variable/ids/to-available-years")
@cache.cached()
def get_variable_ids_to_available_years():
    result = query_engine.variable_ids_to_available_years()
    return result, 200

@app.route("/stats/variable/ids")
@cache.cached()
def get_all_variables():
    result = query_engine.all_variable_ids()
    return result, 200

@app.route("/stats/variable/<variable_id>/compare")
@cache.cached(response_hit_indication=True, query_string=True)
def get_variable_compare(variable_id):
    year_from = int(request.args.get("from"))
    year_to = int(request.args.get("to"))
    compare_method = request.args.get("method", "perc")
    
    if compare_method != "perc":
        return {"error": "Invalid compare method. Only 'perc' currently is supported."}, 400
    
    if (year_from is None or year_to is None) or (year_from == year_to):
        return {"error": "Query params 'from' and 'to' must specified, and be two different integer years"}, 400
    
    result = query_engine.variable_compare_perc(variable_id, year_from, year_to)
    
    if result == []:
        return {"error": "No statistics found for the combination of the specified variable and census years"}, 404

    return result, 200
    
    
@app.route("/stats/variable/<variable_id>/<int:census_year>")
@cache.cached(response_hit_indication=True)
def get_all_map_stats(variable_id, census_year):
    result = query_engine.map_stats(variable_id, census_year)
    
    if result == []:
        return {"error": "No statistics found for the combination of the specified variable and census year"}, 404

    return result, 200

if __name__ == "__main__":
    print("Running a production server at http://localhost:5000")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)
