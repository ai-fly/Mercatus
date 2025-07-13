import logging

from pydantic import BaseModel
from app.llms.model import get_vertex_model
from langgraph.prebuilt import create_react_agent

def create_planner_node(response_format: BaseModel, system_prompt: str):
    """规划节点"""
    logging.info("create  planner agent")
    return create_react_agent(
        name="PlannerAgent",
        prompt=system_prompt,
        model=get_vertex_model(),
        tools=[],
        response_format=response_format,
    )
