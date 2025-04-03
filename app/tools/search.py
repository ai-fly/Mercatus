from typing import Any
from agents import RunContextWrapper, function_tool
from tavily import TavilyClient
from app.config import TAVILY_API_KEY




@function_tool(name_override="search")  
def search_tool(ctx: RunContextWrapper[Any], query: str) -> str:
    """Use this tool to search the web for the given query.

    Args:
        query: The query to search for.
    """

    client = TavilyClient(api_key=TAVILY_API_KEY)
    # invoke tavily search api
    results = client.search(query)
    return str(results)