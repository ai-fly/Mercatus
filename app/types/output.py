from pydantic import BaseModel


class TaskItem(BaseModel):
    task: str
    """具体的单次任务信息"""


class UserQueryPlan(BaseModel):
    tasks: list[TaskItem]
    """基于用户的输入,生成一个计划,指导AI执行任务,计划由多个任务组成."""


class EvaluatorResult(BaseModel):
    status: str
    """任务状态: 完成/部分完成/未完成/失败"""
    
    action: str
    """建议行动: 继续执行计划/重试当前任务/调整任务计划/终止执行"""
    
    overall_status: str
    """整体任务完成状态: 进行中/已完成/需要调整"""
    
    summary: str = ""
    """评估结果的详细说明或总结"""


