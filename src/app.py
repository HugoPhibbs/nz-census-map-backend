import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from src import query_engine
from src.health_check import health_check
from src.utils import get_redis_connection_pool
from src.cached_response import cached_response

load_dotenv()

redis_pool = get_redis_connection_pool()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

CORS(app, origins=["http://localhost:3000", os.environ["FRONTEND_DOMAIN"]])

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"],
    storage_uri="redis://",
    storage_options={"connection_pool": redis_pool},
    strategy="fixed-window",
    swallow_errors=True,
)

app.json.sort_keys = (
    False  # Disable sorting of keys in JSON responses for better performance
)


@app.route("/health")
def get_health():
    healthy, db_ping_time, redis_ping_time = health_check()
    if healthy and db_ping_time is not None and redis_ping_time is not None:
        return {
            "status": "ok",
            "db_ping_time_ms": db_ping_time,
            "redis_ping_time_ms": redis_ping_time,
        }, 200
    else:
        return {"status": "broken"}, 503


@app.route("/area/<area_id>/bounding-box")
@cached_response()
def get_area_bounding_box(area_id):
    result = query_engine.area_bounding_box(area_id)
    if result is None:
        return {"error": "Area not found"}, 404

    return result, 200


@app.route("/area/<area_id>")
@cached_response()
def get_area_info(area_id):
    result = query_engine.area_info(area_id)

    if not result:
        return {"error": "Area not found"}, 404

    return result, 200


@app.route("/stats/area/<area_id>/<int:census_year>")
@cached_response(compress=True)
def get_area_stats(area_id, census_year):
    result = query_engine.area_stats(census_year, area_id)

    if not result:
        return {
            "error": "No statistics found for the specified area and census year"
        }, 404

    return result, 200


@app.route("/stats/variable/avgs/<int:census_year>")
@cached_response(compress=True)
def get_variable_avgs(census_year):
    result = query_engine.variable_averages(census_year)

    if result == {}:
        return {"error": "No statistics found for the specified census year"}, 404

    return result, 200


@app.route("/stats/variable/ids/to-unit")
@cached_response(compress=True)
def get_variable_ids_to_unit():
    result = query_engine.variable_ids_to_unit()
    return result, 200


@app.route("/stats/variable/ids/to-name")
@cached_response(compress=True)
def get_variable_ids_to_name():
    result = query_engine.variable_ids_to_name()
    return result, 200


@app.route("/stats/variable/ids/to-available-years")
@cached_response(compress=True)
def get_variable_ids_to_available_years():
    result = query_engine.variable_ids_to_available_years()
    return result, 200


@app.route("/stats/variable/ids")
@cached_response(compress=True)
def get_all_variables():
    result = query_engine.all_variable_ids()
    return result, 200


@app.route("/stats/variable/<variable_id>/compare")
@cached_response(compress=True, query_string=True)
def get_variable_compare(variable_id):
    year_from = request.args.get("from", type=int)
    year_to = request.args.get("to", type=int)
    method = request.args.get("method", default="delta")

    if (year_from is None or year_to is None) or (year_from == year_to):
        return {
            "error": "Query params 'from' and 'to' must specified, and be two different integer years"
        }, 400

    if method not in ["perc", "delta"]:
        return {"error": "Query param 'method' must be either 'perc' or 'delta'"}, 400

    result = query_engine.variable_compare(variable_id, year_from, year_to, method)

    if result == []:
        return {
            "error": "No statistics found for the combination of the specified variable and census years"
        }, 404

    return result, 200


@app.route("/stats/variable/<variable_id>/<int:census_year>")
@cached_response(compress=True)
def get_all_map_stats(variable_id, census_year):
    result = query_engine.map_stats(variable_id, census_year)

    if len(result) == 0:
        return {
            "error": "No statistics found for the combination of the specified variable and census year"
        }, 404

    return result, 200


if __name__ == "__main__":
    print("Running a production server at http://localhost:5000")
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000, threads=4)
