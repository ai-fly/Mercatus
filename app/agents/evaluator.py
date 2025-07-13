import logging

from pydantic import BaseModel
from app.agents.state import AgentState
from app.llms.model import get_vertex_model
from app.types.output import EvaluatorResult
from app.prompts.evaluator import SYSTEM_PROMPT, USER_PROMPT
from langgraph.prebuilt import create_react_agent


def create_evaluator_node(response_format: BaseModel, system_prompt: str):
    """评估节点"""
    logging.info("create evaluator agent")
    return create_react_agent(
        name="EvaluatorAgent",
        model=get_vertex_model(),
        prompt=SYSTEM_PROMPT,
        tools=[],
        response_format=EvaluatorResult,
    )
