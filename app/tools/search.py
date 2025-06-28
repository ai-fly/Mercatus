from typing import Any
from langchain_core.tools import tool
from tavily import TavilyClient
from app.config import TAVILY_API_KEY


@tool
def search_tool(keyword: str) -> str:
    """Use this tool to search the web url or breif information for the given SEO keyword.

    Args:
        keyword: The keyword to search for.
    """

    client = TavilyClient(api_key=TAVILY_API_KEY)
    # invoke tavily search api
    results = client.search(keyword, max_results=5, include_answer=True,
                            include_raw_content=True, include_images=True)
    if results and "results" in results and len(results["results"]) > 0:
        return str(results["results"])
    return "No results"
