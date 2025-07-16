from tempfile import TemporaryDirectory
from pydantic import BaseModel
from app.llms.model import get_vertex_model
from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits import FileManagementToolkit


def create_executor_node(response_format: BaseModel, system_prompt: str):
    working_dir = TemporaryDirectory()
    toolkit = FileManagementToolkit(root_dir=str(working_dir.name))
    file_tools = toolkit.get_tools()
    return create_react_agent(
        name="ExecutorAgent",
        model=get_vertex_model(),
        prompt=system_prompt,
        response_format=response_format,
        tools=[search_tool, browser_use_tool, *file_tools],
    )
