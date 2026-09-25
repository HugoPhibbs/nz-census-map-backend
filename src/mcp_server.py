from mcp.server import MCPServer
import src.query_engine as query_engine
from typing import TypedDict

mcp = MCPServer("NZ Census Map Server")


class AreaInfo(TypedDict):
    area_code: str
    area_name: str
    area_type: str
    census_year: int


@mcp.tool()
def get_area_info(area_code: str, census_year: int = 2023) -> AreaInfo:
    """Get information about a specific area for a given census year."""
    return query_engine.area_info(census_year, area_code)


class AreaStat(TypedDict):
    area_code: str
    census_year: int
    variable_id: str
    variable_value: float


@mcp.tool()
def get_area_stats(area_code: str, census_year: int = 2023) -> list[AreaStat]:
    """Get all demographic statistics for a specific area for a given census year."""
    return query_engine.area_stats(census_year, area_code)


@mcp.tool()
def get_variable_avgs(census_year: int = 2023) -> dict[str, float]:
    """
    Get the national averages for all demographic variables for a given census year.

    Returns an dictionary mapping variable_ids to national averages.
    """
    return query_engine.variable_averages(census_year)


class VariableInfo(TypedDict):
    variable_id: str
    variable_unit: str
    plain_name: str
    description: str


@mcp.tool()
def get_all_variable_info() -> list[VariableInfo]:
    """
    Get information about all demographic variables.

    Returns a list of dictionaries, each containing information about a demographic variable.

    You can fetch this list to find which demographic variables are available, and to match a natural language description
    E.g. "income level" to the variable ID "median_personal_income". The fields "plain_name" and "description" may be helpful
    """
    return query_engine.all_variable_info()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", stateless_http=True)
