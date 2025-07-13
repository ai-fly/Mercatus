import logging

from pydantic import BaseModel
from app.llms.model import get_vertex_model
from app.prompts.executor import SYSTEM_PROMPT, USER_PROMPT
from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from langgraph.prebuilt import create_react_agent
from app.mcps.mcp_entrypoint import mcp_servers
from app.agents.state import AgentState


def create_executor_node(response_format: BaseModel, system_prompt: str):
    return create_react_agent(
        name="ExecutorAgent",
        model=get_vertex_model(),
        prompt=SYSTEM_PROMPT,
        tools=[search_tool, browser_use_tool, *await mcp_servers.get_tools()]
    )

