import logging
from app.llms.model import get_vertex_model
from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from app.prompts.executor import dynamic_instructions
from langgraph.prebuilt import create_react_agent
from app.mcps.mcp_entrypoint import mcp_servers
from app.agents.state import AgentState


async def executor_node(state: AgentState):
    executor = create_react_agent(
        name="ExecutorAgent",
        model=get_vertex_model(),
        prompt=dynamic_instructions,
        tools=[search_tool, browser_use_tool, *await mcp_servers.get_tools()]
    )

    """执行节点"""
    logging.info("Running executor agent")
            
    # 获取当前任务
    if state["plan"] and state["current_task_index"] < len(state["plan"].tasks):
        current_task = state["plan"].tasks[state["current_task_index"]]
        
        # 创建执行上下文
        from app.types.context import ExecutorContext
        exec_context = ExecutorContext(
            goal=state["user_query"],
            tasks=state["plan"].tasks,
            current_task=current_task,
            finished=False,
            execution_history=state["execution_results"]
        )
        
        # 调用 executor agent（这里需要传递上下文）
        result = await executor.ainvoke({
            "messages": state["messages"]
        }, config={"configurable": {"context": exec_context}})
        
        # 更新状态
        execution_results = state["execution_results"].copy()
        execution_results.append(str(result))
        
        return {
            "current_execution_result": str(result),
            "execution_results": execution_results,
            "current_task_index": state["current_task_index"] + 1,
            "workflow_status": "executing"
        }
    else:
        return {
            "workflow_status": "execution_completed"
        }