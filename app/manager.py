from agents import Runner
from typing import List, Dict, Any

from app.agents.planner import planner_agent
from app.agents.executor import executor_agent 
from app.agents.evaluator import evaluator_agent
from app.types.context import ExecutorContext
from app.types.output import TaskItem, UserQueryPlan


class Manager:
    """管理AI代理工作流的类，协调计划-执行-评估循环"""

    async def run(self, query: str) -> str:
        """
        执行完整的AI代理工作流
        
        Args:
            query: 用户输入的问题
            
        Returns:
            str: 任务完成的结果
        """
        # 1. 使用planner agent生成计划
        plan_result = await Runner.run(planner_agent, query)
        plan: UserQueryPlan = plan_result.final_output_as(UserQueryPlan)
        
        
        # 提取计划中的任务
        tasks = plan.tasks
        if not tasks:
            return "无法为您的问题生成有效的执行计划。"
        
        # 2. 创建执行上下文
        context = ExecutorContext(
            goal=query,
            tasks=tasks,
            finished=False,
            current_task=tasks[0],
            execution_history=[]
        )
        
        results = []
        task_index = 0
        
        # 3. 执行计划-执行-评估循环，直到所有任务完成
        while not context.finished and task_index < len(tasks):
            # 更新当前任务
            context.current_task = tasks[task_index]
            
            # 执行当前任务
            executor_result = await Runner.run(executor_agent, context=context)
            
            # 记录执行历史
            execution_result = f"任务 {task_index + 1}: {context.current_task.task}\n执行结果: {executor_result.final_output}"
            context.execution_history.append(execution_result)
            
            # 评估执行结果
            evaluator_result = await Runner.run(evaluator_agent, context=context)
            eval_output = evaluator_result.final_output
            
            # 根据评估结果决定下一步操作
            if "完成" in eval_output:
                # 任务完成，保存结果并继续下一任务
                results.append(f"任务 {task_index + 1} 已完成: {context.current_task.task}")
                task_index += 1
            elif "重试" in eval_output:
                # 需要重试当前任务，不增加索引
                context.execution_history.append(f"评估结果: 需要重试任务 {task_index + 1}")
            elif "调整" in eval_output:
                # 需要重新规划，重新调用planner
                context.execution_history.append(f"评估结果: 需要调整计划")
                new_plan_result = await Runner.run(planner_agent, f"{query}\n基于执行历史进行计划调整: {context.execution_history}")
                new_plan = new_plan_result.output
                
                # 更新任务列表
                tasks = new_plan.tasks
                context.tasks = tasks
                
                # 如果没有任务，结束循环
                if not tasks:
                    context.finished = True
                    break
                    
                # 重置任务索引
                task_index = 0
            elif "终止" in eval_output:
                # 终止执行
                context.finished = True
                results.append(f"执行终止: {eval_output}")
                break
            
            # 检查是否所有任务都已完成
            if task_index >= len(tasks):
                context.finished = True
        
        # 4. 返回执行结果
        if context.finished:
            return "\n".join(results) + "\n\n最终结果：" + context.execution_history[-1].split("执行结果: ")[-1]
        else:
            return "任务未能完全执行完成。当前进度：\n" + "\n".join(results)
        