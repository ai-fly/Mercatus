from agents import Agent
from agents.model_settings import ModelSettings

from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from app.prompts.executor import dynamic_instructions
from app.mcps.file import file_mcp_server

executor_agent = Agent(
    name="ExecutorAgent",
    instructions=dynamic_instructions,
    mcp_servers=[file_mcp_server],
    tools=[search_tool, browser_use_tool],
    model_settings=ModelSettings(tool_choice="required"),
)