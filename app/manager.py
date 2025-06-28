from app.agents.planner import  planner_node
from app.agents.executor import executor_node
from app.agents.evaluator import evaluator_node
from app.utils.logging import setup_logger
from app.agents.state import AgentState
from langgraph.graph import StateGraph, START, END

class Manager:
    """Class that manages AI agent workflow, coordinating the plan-execute-evaluate cycle"""

    def __init__(self):
        """Initialize manager and set up logging"""
        self.logger = setup_logger(name="manager")

    async def run(self, query: str) -> str:
        """
        Execute the complete AI agent workflow

        Args:
            query: User input question

        Returns:
            str: Task completion result
        """
        self.logger.info(f"Starting to process user query: {query}")


        # 条件路由函数
        def should_continue(state: AgentState):
            """决定是否继续执行任务"""
            if state["workflow_status"] == "planning_completed":
                return "executor"
            elif state["workflow_status"] == "executing":
                # 检查是否还有更多任务
                if state["plan"] and state["current_task_index"] < len(state["plan"].tasks):
                    return "executor"  # 继续执行下一个任务
                else:
                    return "evaluator"  # 所有任务完成，进入评估
            elif state["workflow_status"] in ["execution_completed", "evaluating"]:
                return "evaluator"
            else:
                return END

        # 构建状态图
        builder = StateGraph(AgentState)
        
        # 添加节点
        builder.add_node("planner", planner_node)
        builder.add_node("executor", executor_node)
        builder.add_node("evaluator", evaluator_node)
        
        # 添加边
        builder.add_edge(START, "planner")
        builder.add_conditional_edges(
            "planner",
            should_continue,
            {
                "executor": "executor",
                "evaluator": "evaluator",
                END: END
            }
        )
        builder.add_conditional_edges(
            "executor",
            should_continue,
            {
                "executor": "executor",
                "evaluator": "evaluator",
                END: END
            }
        )
        builder.add_edge("evaluator", END)

        # 编译并运行
        app = builder.compile()
        
        # 初始状态
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "user_query": query,
            "plan": {},
            "current_task_index": 0,
            "execution_results": [],
            "current_execution_result": None,
            "evaluation_result": None,
            "workflow_status": "planning",
            "error_message": None
        }
        
        result = await app.ainvoke(initial_state)
        
        # 返回最终结果
        if result["evaluation_result"]:
            return result["evaluation_result"].summary
        elif result["execution_results"]:
            return result["execution_results"][-1]
        else:
            return "Task completed but no results available"