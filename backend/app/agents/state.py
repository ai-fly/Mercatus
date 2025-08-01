from dataclasses import dataclass
from typing import Annotated, List, Union
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.experts.expert import ExpertTask
from app.types.output import TaskItem, UserQueryPlan, EvaluatorResult


@dataclass
class ExecutorContext:
    goal: str
    """User's goal"""

    tasks: list[TaskItem]
    """All tasks"""

    finished: bool
    """Whether the task is completed"""

    current_task: TaskItem
    """The task currently being executed"""

    execution_history: list[str]
    """Execution history"""


class AgentState(TypedDict):
    """State shared between all agents in the workflow"""

    task: ExpertTask

    feedbacks: list[str]

    
