import logging
from app.agents.state import AgentState
from app.llms.model import get_vertex_model
from app.types.output import EvaluatorResult
from app.prompts.evaluator import SYSTEM_PROMPT, USER_PROMPT
from langgraph.prebuilt import create_react_agent


async def evaluator_node(state: AgentState):
    """评估节点"""
    logging.info("Running evaluator agent")
    evaluator = create_react_agent(
        name="EvaluatorAgent",
        model=get_vertex_model(),
        prompt=SYSTEM_PROMPT,
        tools=[],
        response_format=EvaluatorResult,
    )

    # 创建评估上下文
    eval_context = {
        "goal": state["user_query"],
        "tasks": [task.task for task in state["plan"].tasks],
        "current_task": state["plan"].tasks[state["current_task_index"]].task if state["plan"] and state["current_task_index"] < len(state["plan"].tasks) else "No current task",
        "execution_history": state["execution_results"]
    }

    # 调用 evaluator agent
    result = await evaluator.ainvoke(
        {"messages": [{"role": "user", "content": USER_PROMPT.format(**eval_context)}]},
    )

    return {"workflow_status": "success"}
