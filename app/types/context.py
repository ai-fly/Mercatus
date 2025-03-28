

from dataclasses import dataclass

from app.types.output import TaskItem


@dataclass
class ExecutorContext():
    goal: str
    """用户的目标"""
    
    tasks: list[TaskItem]
    """所有任务"""

    finished: bool
    """是否完成任务"""

    current_task: TaskItem
    """当前要执行的任务"""

    execution_history: list[str]
    """执行历史"""
    