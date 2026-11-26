import hmac
import os
from typing import Literal, TypedDict

from mcp.server import MCPServer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src import query_engine
from src.search_variables import search_variables

mcp = MCPServer(
    "NZ Census Map Server",
    instructions="""
    A querying interface for NZ Census Data for the years 2013, 2018, 2023

    Census data is partitioned into geographical areas types. In ascending order of size these are:  
    1. SA1: Containing around 100-200 people. Equivalent to a small neighbourhood or sparse rural area
    2. SA2: Contains constituent SA1s. Equivalent to a neighbourhood
    3. SA3: Contains SA2s. Equivalent to a group of neighbourhoods
    4. TA: Containing SA3s. A much larger area such as entire cities or regions. 
    """,
)

EXPECTED_TOKEN = os.getenv("MCP_BEARER_TOKEN")
if not EXPECTED_TOKEN:
    raise ValueError("MCP_BEARER_TOKEN environment variable is not set")

EXPECTED_AUTH = f"Bearer {EXPECTED_TOKEN}".encode()


async def check_auth(request, call_next):
    provided_auth = request.headers.get("authorization", "").encode()

    if not hmac.compare_digest(provided_auth, EXPECTED_AUTH):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    return await call_next(request)


# Adding 0.0.0.0 allows the MCP server to be accessed from outside the container
# I.e. it turns on listening to all outside interfaces (default is only localhost)
app = mcp.streamable_http_app(stateless_http=True, host="0.0.0.0")
app.add_middleware(BaseHTTPMiddleware, dispatch=check_auth)

AREA_TYPE = Literal["SA1", "SA2", "SA3", "TA"]


class Area(TypedDict):
    area_id: str
    area_name: str | None  # SA1 areas have no name
    area_type: AREA_TYPE


class DemographicData(TypedDict):
    area_id: str
    variable_id: str
    variable_value: float


class DemographicVariable(TypedDict):
    variable_id: str
    variable_unit: str
    plain_name: str
    description: str


@mcp.tool()
def get_area_info(area_id: str) -> Area:
    """
    Get information about a specific area

    Please note, for areas that are "SA1", there are no names (they are only numbered).
    So don't bother trying to get their names. If an area_name is None/null assume it is an SA1 area.
    """
    return query_engine.area_info(area_id)


@mcp.tool()
def get_area_info_bulk(area_ids: list[str]) -> list[Area]:
    """
    Get information about a areas with the given ids

    Please note, for areas that are "SA1", there are no names (they are only numbered).
    So don't bother trying to get their names. If an area_name is None/null assume it is an SA1 area.
    """
    return query_engine.area_info_bulk(area_ids)


@mcp.tool()
def get_variable_avgs(census_year: int = 2023) -> dict[str, float]:
    """
    Get the national averages for all demographic variables for a given census year.

    Returns an dictionary mapping variable_ids to national averages.
    """
    return query_engine.variable_averages(census_year)


@mcp.tool()
def get_all_variable_info() -> list[DemographicVariable]:
    """
    Get information about all demographic variables.

    Returns a list of dictionaries, each containing information about a demographic variable.

    You can fetch this list to find which demographic variables are available, and to match a natural language description
    E.g. "income level" to the variable ID "median_personal_income". The fields "plain_name" and "description" may be helpful
    """
    return query_engine.all_variable_info()


@mcp.tool()
def get_variable_ids_to_unit() -> dict[str, str]:
    """
    Get a mapping of variable IDs to their corresponding units.

    Returns a dictionary where the keys are variable IDs and the values are the units associated with those variables.
    """
    return query_engine.variable_ids_to_unit()


@mcp.tool()
def get_variable_ids_to_name() -> dict[str, str]:
    """
    Get a mapping of variable IDs to their corresponding plain names.

    Returns a dictionary where the keys are variable IDs and the values are the plain names associated with those variables.

    Format of the returned dictionary:
    {
        "variable_id_1": "plain_name_1",
        "variable_id_2": "plain_name_2"
    }
    """
    return query_engine.variable_ids_to_name()


@mcp.tool()
def get_variable_values_for_areas(
    area_ids: list[str],
    census_year: int = 2023,
    variable_ids_to_keep: list[str] | None = None,
) -> dict[str, dict[str, float | None]]:
    """
    Get the value for specific demographic variables for specific areas and a census year.

    Parameters:
    - area_ids (list[str]): List containing the IDs of the areas you're interested in.
    - census_year (int): The census year to query. Default is 2023.
    - variables_ids_to_keep (list[str]): Optional, leave empty for all variables OR specify a list of variable IDs to keep in the results.

    Returns:
    A dict containing stats for each area. Format: {area_id: {variable_id: variable_value}, ... }. E.g. {area_id1: {{"median_age": 63}, {"pop_resident_usual": 12087}}, area_id2: {...}}

    Example:
    values = get_variable_values_for_areas(["001"], 2023, ["median_age"])
    values = get_variable_values_for_areas(["001", "002"], 2023, ["median_personal_income", "median_age"])
    """
    return query_engine.variable_values_for_areas(
        area_ids, census_year, variable_ids_to_keep
    )


@mcp.tool()
def get_all_variable_ids() -> list[str]:
    """
    Get a list of all demographic variable IDs.

    Returns a list of strings, each representing a unique variable ID.

    Example of the returned list:
    [
        "median_personal_income",
        "avg_hours_worked_per_week",
        "perc_ethnicity_pacific",
        ...
    ]
    """
    return query_engine.all_variable_ids()


@mcp.tool()
def get_all_variable_stats(
    variable_ids: list[str],
    census_year: int = 2023,
    area_type: AREA_TYPE | None = None,
    sort_order: Literal["asc", "desc"] | None = None,
    contained_in_area_id: str | None = None,
    top_k: int | None = None,
) -> list[DemographicData]:
    """
    Get all demographic statistics for specified variables across all areas for a given census year.

    Parameters:
    - variable_ids (list[str]): The IDs of the demographic variable to fetch for
    - census_year (int): The census year to query. Default is 2023.
    - area_type (AREA_TYPE | None): Optional. Filter areas by type (e.g., "SA1", "SA2", "SA3", "TA"). If None, all area types are included. Default is None.
    - sort_order ("asc" | "desc" | None): Optional. Sort results by value. Areas with no value are excluded when sorting. If None, results are unsorted. Default is None.
    - contained_in_area_id (str | None): Optional. Specify to restrict results for areas that are contained in another area with the given id. Should only be SA2, SA3 or TA areas - SA1 don't contain any smaller areas
    - top_k (int | None): Optional. Return only the first k results. If set without sort_order, results are sorted descending (highest values first). Default is None.

    Returns:
    A list of dictionaries, each containing demographic data points for the specified variable

    Example of the returned list:
    [
        {
            "area_id": "001",
            "variable_id": "pop_resident_usual",
            "variable_value": 55000.0
        },
        {
            "area_id": "002",
            "variable_id": "pop_resident_usual",
            "variable_value": 60000.0
        },
        ...
    ]
    """
    return query_engine.all_variable_stats(
        variable_ids, census_year, area_type, sort_order, contained_in_area_id, top_k
    )


@mcp.tool()
def fuzzy_search_areas_by_name(
    query: str, area_type: str | None = None, top_k: int = 10
) -> list[dict[str, str]]:
    """
    Fuzzy searches areas by their name with a query string

    Can be optionally filtered by their area type

    Returns the top_k matching results as a list of dicts, where each dict has keys for area_id, area_name, area_type, ordered by their relevance
    """
    return query_engine.fuzzy_search_areas_by_name(query, area_type, top_k)


@mcp.tool()
def search_variables_by_query(query: str, top_k: int = 10) -> list[str]:
    """
    Searches variables according to a brief query, returns the top k matching variables

    Queries should be short conceptual phrases, such as "asian community" or "elderly population", not entire sentences

    Returns the top_k matching results as a list of matching variable ids 
    """
    return search_variables(query, top_k)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
