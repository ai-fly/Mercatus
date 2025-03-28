
from pydantic import BaseModel


class TaskItem(BaseModel):
    task: str
    """具体的单次任务信息"""


class UserQueryPlan(BaseModel):
    tasks: list[TaskItem]
    """基于用户的输入,生成一个计划,指导AI执行任务,计划由多个任务组成."""


