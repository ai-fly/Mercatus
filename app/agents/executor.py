from pydantic import BaseModel
from app.llms.model import get_vertex_model
from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from langgraph.prebuilt import create_react_agent
from app.mcps.mcp_entrypoint import get_tools


def create_executor_node(response_format: BaseModel, system_prompt: str):
    return create_react_agent(
        name="ExecutorAgent",
        model=get_vertex_model(),
        prompt=system_prompt,
        response_format=response_format,
        tools=[search_tool, browser_use_tool, *get_tools()],
    )
