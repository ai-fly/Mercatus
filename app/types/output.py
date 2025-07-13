from dataclasses import Field
from pydantic import BaseModel


class AgentPlannerResultItem(BaseModel):
    """
    Specific single task information
    """
    task_name: str = Field(description="The name of the task")
    task_description: str = Field(description="The description of the task")



class AgentPlannerResult(BaseModel):
    """
    Based on user input, generate a plan to guide AI in executing tasks, consisting of multiple tasks.
    """
    tasks: list[AgentPlannerResultItem] = Field(description="The tasks of the plan")


class AgentEvaluatorResult(BaseModel):
    """
    Evaluate executor agent's execution result
    """
    unfinished_tasks: list[AgentPlannerResultItem] = Field(description="The tasks that are not finished")


class AgentExecutorResultItem(BaseModel):
    """
    The result of a single task execution
    """
    task_name: str = Field(description="The name of the task")
    task_description: str = Field(description="The description of the task")
    task_result: str = Field(description="The result of the execution")


class AgentExecutorResult(BaseModel):
    """
    The result of the execution of a plan, consisting of multiple tasks.
    """
    items: list[AgentExecutorResultItem] = Field(description="The items of the execution")
