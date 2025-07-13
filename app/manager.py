import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from app.agents.evaluator import create_evaluator_node
from app.agents.executor import create_executor_node
from app.agents.planner import create_planner_node
from app.config import settings
from app.types.context import AppContext
from app.types.output import AgentEvaluatorResult, AgentExecutorResult, AgentPlannerResult


class AgentState(TypedDict):
    """Agent state management"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    planner_result: AgentPlannerResult
    executor_result: AgentExecutorResult
    evaluator_result: AgentEvaluatorResult


def should_continue(state: AgentState) -> str:
    """Conditional routing function"""
    
    """Decide whether to continue executing tasks"""
    evaluator_result = state.get("evaluator_result")
    
    # Check if there are more tasks
    if evaluator_result and len(evaluator_result.unfinished_tasks) > 0:
        return "executor"  # Continue executing next task
    else:
        return "evaluator"  # All tasks completed, proceed to evaluation


def create_agent_workflow(context: AppContext):
    """Create agent workflow"""
    
    # Build state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", create_planner_node(AgentPlannerResult, ""))
    workflow.add_node("executor", create_executor_node(AgentExecutorResult, ""))
    workflow.add_node("evaluator", create_evaluator_node(AgentEvaluatorResult, ""))
    
    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges(
        "executor",
        should_continue,
        {
            "executor": "executor",
            "evaluator": "evaluator",
        },
    )
    workflow.add_edge("evaluator", END)
    
    return workflow


class AgentManager:
    """Agent manager for coordinating multi-agent workflows"""
    
    def __init__(self, context: AppContext):
        self.context = context
        self.workflow = create_agent_workflow(context)
        
    async def run(self, input_data: dict) -> dict:
        """Run the agent workflow"""
        
        # Compile and run
        app = self.workflow.compile()
        
        # Initial state
        initial_state = {
            "messages": [{"role": "user", "content": str(input_data)}],
            "planner_result": None,
            "executor_result": None,
            "evaluator_result": None
        }
        
        try:
            result = await app.ainvoke(initial_state)
            
            # Return final result
            return {
                "status": "success",
                "planner_result": result.get("planner_result"),
                "executor_result": result.get("executor_result"),
                "evaluator_result": result.get("evaluator_result")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }