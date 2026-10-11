import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS

from src import query_engine

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])

app.config["COMPRESS_MIN_SIZE"] = 450
compress = Compress(app)

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

app.json.sort_keys = False  # Disable sorting of keys in JSON responses for better performance

@app.route("/health")
def health_check():
    healthy, db_ping_time = query_engine.health_check()
    if healthy and db_ping_time is not None:
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
    year_from = request.args.get("from", type=int)
    year_to = request.args.get("to", type=int)
    method = request.args.get("method", default="delta")
    
    if (year_from is None or year_to is None) or (year_from == year_to):
        return {"error": "Query params 'from' and 'to' must specified, and be two different integer years"}, 400
    
    if method not in ["perc", "delta"]:
        return {"error": "Query param 'method' must be either 'perc' or 'delta'"}, 400
    
    result = query_engine.variable_compare(variable_id, year_from, year_to, method)
    
    if result == []:
        return {"error": "No statistics found for the combination of the specified variable and census years"}, 404

    return result, 200
    

@app.route("/stats/variable/<variable_id>/<int:census_year>")
@cache.cached(response_hit_indication=True)
def get_all_map_stats(variable_id, census_year):
    result = query_engine.map_stats(variable_id, census_year)
    
    if len(result) == 0:
        return {"error": "No statistics found for the combination of the specified variable and census year"}, 404

    return result, 200

if __name__ == "__main__":
    print("Running a production server at http://localhost:5000")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)
