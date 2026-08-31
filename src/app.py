from flask import Flask, request
from flask_cors import CORS
from flask import send_file
from waitress import serve
from scripts.db_setup import get_db_connection_pool
from psycopg.rows import dict_row
from pypika import Query, Table

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


@app.route("/stats/region/<region_id>")
def get_region_stats(region_id):
    pass


@app.route("/stats/region/all")
def get_all_regions_stats():
    variables_param = request.args.get('variables')

    if not variables_param:
        return {"error": "No variables specified, please use the query parameter 'variables' to specify the variables you want to retrieve."}, 400

    variables = variables_param.split(',')

    demographic_data = Table('demographic_data')

    q = Query.from_(demographic_data).select('*').where(demographic_data.variable_name.isin(variables))

    if area_type := request.args.get('area_type'):
        areas = Table('areas')
        q = q.join(areas).on(
            (demographic_data.area_code == areas.area_code) &
            (demographic_data.census_year == areas.census_year)
        ).where(areas.area_type == area_type)

    with get_db_connection_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q.get_sql())
            result = cur.fetchall()
            return result, 200


@app.route('/area-boundaries.pmtiles')
def map():
    return send_file(
        "../data/area-boundaries.pmtiles",
        mimetype='application/octet-stream',
        conditional=True
    )


if __name__ == '__main__':
    # app.run(debug=True, threaded=True)

    print("Running a production server at http://localhost:5000")
    serve(app, host='0.0.0.0', port=5000, threads=4)
