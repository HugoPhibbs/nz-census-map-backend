import hmac
import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_caching import Cache
from flask_cors import CORS

from src import query_engine

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", os.getenv("FRONTEND_DOMAIN")])

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300})

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError(
        "BEARER_TOKEN environment variable is not set. Please set it in your .env file."
    )

EXPECTED_AUTH = f"Bearer {os.getenv('BEARER_TOKEN')}".encode()


@app.before_request
def check_auth():
    if request.method == "OPTIONS":
        return

    provided_auth = request.headers.get("Authorization", "").encode()

    if not hmac.compare_digest(provided_auth, EXPECTED_AUTH):
        return {"error": "Unauthorized"}, 401


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
    drop_pop_data = request.args.get("drop_pop_data", "false").lower() == "true"

    result = query_engine.all_variable_stats(
        variable_id,
        census_year,
        request.args.get("area_type"),
        drop_pop_data=drop_pop_data,
    )

    return result, 200


if __name__ == "__main__":
    print("Running a production server at http://localhost:5000")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)
