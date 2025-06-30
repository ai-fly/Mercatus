import logging
from app.agents.state import AgentState
from app.llms.model import get_vertex_model
from app.types.output import EvaluatorResult
from app.prompts.evaluator import dynamic_instructions
from langgraph.prebuilt import create_react_agent


async def evaluator_node(state: AgentState):
    """评估节点"""
    logging.info("Running evaluator agent")
    evaluator = create_react_agent(
        name="EvaluatorAgent",
        model=get_vertex_model(),
        prompt=dynamic_instructions,
        tools=[],
        response_format=EvaluatorResult,
    )

    # 创建评估上下文
    if state["plan"]:
        from app.types.context import ExecutorContext

        eval_context = ExecutorContext(
            goal=state["user_query"],
            tasks=state["plan"].tasks,
            current_task=(
                state["plan"].tasks[state["current_task_index"] - 1]
                if state["current_task_index"] > 0
                else state["plan"].tasks[0]
            ),
            finished=state["current_task_index"] >= len(state["plan"].tasks),
            execution_history=state["execution_results"],
        )

        # 调用 evaluator agent
        result = await evaluator.ainvoke(
            {"messages": state["messages"]},
        )

        return {"evaluation_result": result, "workflow_status": "completed"}

    return {
        "workflow_status": "failed",
        "error_message": "No plan available for evaluation",
    }
