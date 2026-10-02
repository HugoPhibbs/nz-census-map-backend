import hmac
import os
from typing import Literal, TypedDict

from mcp.server import MCPServer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src import query_engine

mcp = MCPServer("NZ Census Map Server")

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
    area_code: str
    area_name: str | None  # SA1 areas have no name
    area_type: AREA_TYPE
    census_year: int


class DemographicData(TypedDict):
    area_code: str
    census_year: int
    variable_id: str
    variable_value: float


class DemographicVariable(TypedDict):
    variable_id: str
    variable_unit: str
    plain_name: str
    description: str


@mcp.tool()
def get_area_info(area_code: str, census_year: int = 2023) -> Area:
    """
    Get information about a specific area for a given census year.

    Please note, for areas that are "SA1", there are no names (they are only numbered).
    So don't bother trying to get their names. If an area_name is None/null assume it is an SA1 area.
    """
    return query_engine.area_info(census_year, area_code)

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
def get_variable_values_for_area(
    area_code: str, census_year: int = 2023, variables_ids_to_keep: str | list[str] | None = None
) -> float | None:
    """
    Get the value of a specific demographic variable for a specific area and census year.

    Parameters:
    - area_code (str): The code of the area.
    - census_year (int): The census year to query. Default is 2023.
    - variables_ids_to_keep (str | list[str]): Optional, leave empty for all variables OR specify a single variable ID (str) or a list of variable IDs (list[str]) to keep in the results.

    Returns:
    The value of the specified demographic variable for the given area and census year, or None if not available.
    
    Example:
    value = get_variable_values_for_area("001", "median_age")
    value = get_variable_values_for_area("001", ["median_personal_income", "median_age"], 2023)
    """
    if isinstance(variables_ids_to_keep, str):
        variables_ids_to_keep = [variables_ids_to_keep]
    return query_engine.variable_values_for_area(area_code, census_year, variables_ids_to_keep)



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
    variable_id: str,
    census_year: int = 2023,
    area_type: AREA_TYPE | None = None,
    sort_order: Literal["asc", "desc"] | None = None,
    top_k: int | None = None,
) -> list[DemographicData]:
    """
    Get all demographic statistics for a specific variable across all areas for a given census year.

    Parameters:
    - variable_id (str): The ID of the demographic variable.
    - census_year (int): The census year to query. Default is 2023.
    - area_type (AREA_TYPE | None): Optional. Filter areas by type (e.g., "SA1", "SA2", "SA3", "TA"). If None, all area types are included. Default is None.
    - sort_order ("asc" | "desc" | None): Optional. Sort results by value. Areas with no value are excluded when sorting. If None, results are unsorted. Default is None.
    - top_k (int | None): Optional. Return only the first k results. If set without sort_order, results are sorted descending (highest values first). Default is None.

    Returns:
    A list of dictionaries, each containing demographic data points for the specified variable
    
    Example of the returned list:
    [
        {
            "area_code": "001",
            "census_year": 2023,
            "variable_id": "median_personal_income",
            "variable_value": 55000.0
        },
        {
            "area_code": "002",
            "census_year": 2023,
            "variable_id": "median_personal_income",
            "variable_value": 60000.0
        },
        ...
    ]
    """
    return query_engine.all_variable_stats(
        variable_id, census_year, area_type, sort_order, top_k
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
