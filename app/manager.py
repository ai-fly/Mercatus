from agents import Runner
from typing import List, Dict, Any

from app.agents.planner import planner_agent
from app.agents.executor import executor_agent 
from app.agents.evaluator import evaluator_agent
from app.types.context import ExecutorContext
from app.types.output import TaskItem, UserQueryPlan, EvaluatorResult


class Manager:
    """Class that manages AI agent workflow, coordinating the plan-execute-evaluate cycle"""

    async def run(self, query: str) -> str:
        """
        Execute the complete AI agent workflow
        
        Args:
            query: User input question
            
        Returns:
            str: Task completion result
        """
        # 1. Generate plan using planner agent
        plan_result = await Runner.run(planner_agent, input=query)
        plan: UserQueryPlan = plan_result.final_output_as(UserQueryPlan)
        
        # Extract tasks from plan
        tasks = plan.tasks
        if not tasks:
            return "Unable to generate a valid execution plan for your question."
        
        # 2. Create execution context
        context = ExecutorContext(
            goal=query,
            tasks=tasks,
            finished=False,
            current_task=tasks[0],
            execution_history=[]
        )
        
        results = []
        task_index = 0
        
        # 3. Execute plan-execute-evaluate loop until all tasks are completed
        while not context.finished and task_index < len(tasks):
            # Update current task
            context.current_task = tasks[task_index]
            
            # Execute current task
            executor_result = await Runner.run(executor_agent, input=context.current_task.task, context=context)
            
            # Record execution history
            execution_result = f"Task {task_index + 1}: {context.current_task.task}\nExecution Result: {executor_result.final_output}"
            context.execution_history.append(execution_result)
            
            # Evaluate execution result
            evaluator_result = await Runner.run(evaluator_agent, input=f"last_task: {context.current_task}, execution_result: {execution_result}, please evaluate the result.", context=context)
            eval_output: EvaluatorResult = evaluator_result.final_output_as(EvaluatorResult)
            
            # Determine next action based on evaluation result
            if eval_output.status == "completed":
                # Task completed, save result and continue to next task
                results.append(f"Task {task_index + 1} completed: {context.current_task.task}")
                task_index += 1
            elif eval_output.action == "continue_execution_plan":
                # Continue with the next task
                results.append(f"Task {task_index + 1} completed: {context.current_task.task}")
                task_index += 1
            elif eval_output.action == "retry_current_task":
                # Need to retry current task, don't increment index
                context.execution_history.append(f"Evaluation Result: Need to retry task {task_index + 1}")
            elif eval_output.action == "adjust_task_plan":
                # Need to replan, call planner again
                context.execution_history.append(f"Evaluation Result: Need to adjust plan")
                new_plan_result = await Runner.run(planner_agent, f"{query}\nAdjust plan based on execution history: {context.execution_history}")
                new_plan: UserQueryPlan = new_plan_result.final_output_as(UserQueryPlan)
                
                # Update task list
                tasks = new_plan.tasks
                context.tasks = tasks
                
                # If no tasks, end loop
                if not tasks:
                    context.finished = True
                    break
                    
                # Reset task index
                task_index = 0
            elif eval_output.action == "terminate_execution":
                # Terminate execution
                context.finished = True
                results.append(f"Execution terminated: {eval_output.summary}")
                break
            
            # Check if all tasks are completed
            if task_index >= len(tasks):
                context.finished = True
        
        # 4. Return execution results
        if context.finished:
            return "\n".join(results) + "\n\nFinal Result: " + context.execution_history[-1].split("Execution Result: ")[-1]
        else:
            return "Tasks could not be fully completed. Current progress:\n" + "\n".join(results)
        