import logging
from app.agents.state import AgentState
from app.llms.model import get_vertex_model
from app.types.output import UserQueryPlan
from app.prompts.planner import PROMPT
from langgraph.prebuilt import create_react_agent

async def planner_node(state: AgentState):
    """规划节点"""
    logging.info("Running planner agent")
    planner = create_react_agent(
        name="PlannerAgent",
        prompt=PROMPT,
        model=get_vertex_model(),
        tools=[],
        response_format=UserQueryPlan,
    )

    # 调用 planner agent
    result = await planner.ainvoke(
        {"messages": [{"role": "user", "content": state["user_query"]}]}
    )

    # 更新状态
    return {
        "plan": result,
        "workflow_status": "planning_completed",
        "current_task_index": 0
    }
