from dataclasses import dataclass
from typing import Annotated, List, Union
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

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

    # 消息历史
    messages: Annotated[List[AnyMessage], add_messages]

    # 用户原始查询
    user_query: str

    # 规划阶段的输出
    plan: UserQueryPlan | None
    current_task_index: int

    # 执行阶段的状态
    execution_results: List[str]
    current_execution_result: str | None

    # 评估阶段的输出
    evaluation_result: EvaluatorResult | None

    # 整体工作流状态
    workflow_status: str  # "planning", "executing", "evaluating", "completed", "failed"

    # 错误信息
    error_message: str | None

    # 添加必需字段
    remaining_steps: int

    structured_response: Union[UserQueryPlan, EvaluatorResult, None]
