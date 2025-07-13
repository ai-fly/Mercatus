import logging
from app.agents.evaluator import create_evaluator_node
from app.agents.executor import create_executor_node
from app.agents.planner import create_planner_node
from app.experts.expert import ExpertBase, ExpertTask
from app.config import settings
from app.experts.prompts.marketing_planner_prompt import EVALUATOR_TASK_PROMPT, EXECUTOR_SYSTEM_PROMPT, EXECUTOR_TASK_PROMPT, PLANNER_SYSTEM_PROMPT, PLANNER_TASK_PROMPT
from app.types.output import AgentEvaluatorResult, AgentExecutorResult, AgentPlannerResult


class MarketingPlannerResult(AgentPlannerResult):
    """
    营销策略专家任务
    """

class MarketingPlannerEvaluatorResult(AgentEvaluatorResult):
    """
    营销策略专家任务评估结果
    """

class MarketingPlannerExecutorResult(AgentExecutorResult):
    """
    营销策略专家任务执行结果
    """


class MarketingPlannerExpert(ExpertBase):
    """
    营销策略专家，负责根据用户需求和平台政策，生成营销策略
    """
    def __init__(self):
        super().__init__("Jeff", "Jeff is a marketing planner expert")
        self.inbox_topic = f"{settings.rocketmq_topic_prefix}_inbox_jeff"

    async def run(self, task: ExpertTask):
        # 1. Generate a marketing plan
        planner_task_prompt = PLANNER_TASK_PROMPT.format(**task.model_dump(mode="json"))
        plan_result: MarketingPlannerResult = await self.planner_agent.ainvoke(messages=[{"role": "user", "content": planner_task_prompt}])

        # 2. Execute the marketing plan
        total_tasks = "\n\n".join([f"task_name: {task.task_name}\ntask_description: {task.task_description}\ntask_goal: {task.task_goal}" for task in plan_result.tasks])

        unfinished_tasks: list[MarketingPlannerEvaluatorResult] = []
        for _ in range(self.retries):
            unfinished_tasks_prompt = "\n\n".join([f"task_name: {task.task_name}\ntask_description: {task.task_description}" for task in unfinished_tasks])

            executor_task_prompt = EXECUTOR_TASK_PROMPT.format(total_tasks=total_tasks, unfinished_tasks=unfinished_tasks_prompt)
            executor_result: MarketingPlannerExecutorResult = await self.executor_agent.ainvoke(messages=[{"role": "user", "content": executor_task_prompt}])

            # 3. Evaluate the marketing plan
            executor_results_prompt = "\n\n".join([f"task_name: {item.task_name}\ntask_description: {item.task_description}\ntask_result: {item.task_result}" for item in executor_result.items])
            evaluator_task_prompt = EVALUATOR_TASK_PROMPT.format(
                tasks=total_tasks, results=executor_results_prompt
            )
            evaluator_result: MarketingPlannerEvaluatorResult = await self.evaluator_agent.ainvoke(messages=[{"role": "user", "content": evaluator_task_prompt}])

            if len(evaluator_result.unfinished_tasks) == 0:
                logging.info("Marketing plan is finished")
                break
            else:
                logging.info("Marketing plan is not finished, retrying...")
                unfinished_tasks = evaluator_result.unfinished_tasks

    def  create_agents(self):
        self.planner_agent = create_planner_node(MarketingPlannerResult, PLANNER_SYSTEM_PROMPT)
        self.executor_agent = create_executor_node(MarketingPlannerExecutorResult, EXECUTOR_SYSTEM_PROMPT)
        self.evaluator_agent = create_evaluator_node(MarketingPlannerEvaluatorResult, EVALUATOR_SYSTEM_PROMPT)
