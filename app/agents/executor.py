import logging
from app.llms.model import get_vertex_model
from app.prompts.executor import SYSTEM_PROMPT, USER_PROMPT
from app.tools.browser import browser_use_tool
from app.tools.search import search_tool
from langgraph.prebuilt import create_react_agent
from app.mcps.mcp_entrypoint import mcp_servers
from app.agents.state import AgentState


async def executor_node(state: AgentState):
    executor = create_react_agent(
        name="ExecutorAgent",
        model=get_vertex_model(),
        prompt=SYSTEM_PROMPT,
        tools=[search_tool, browser_use_tool, *await mcp_servers.get_tools()]
    )

    """执行节点"""
    logging.info("Running executor agent")

    # 获取当前任务
    if state["plan"] and len(state["plan"].tasks) > 0:
        for current_task in state["plan"].tasks:
            exec_context = {
                "goal": state["user_query"],
                "tasks": [task.task for task in state["plan"].tasks],
                "current_task": current_task.task
            }

            # 调用 executor agent（这里需要传递上下文）
            result = await executor.ainvoke({
                "messages": [{"role": "user", "content": USER_PROMPT.format(**exec_context)}]
            })

    return {
        "workflow_status": "execution_completed"
    }
