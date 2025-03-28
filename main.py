import os
from agents import Agent, Runner, set_default_openai_api, set_tracing_disabled
from browser_use import Agent as BrowserAgent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContext
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from agents import set_default_openai_client
from pydantic import SecretStr
from app.config import BASIC_LLM_API_KEY, BASIC_LLM_URL
from app.mcps.file import file_mcp_server
from agents.mcp import MCPServer, MCPServerStdio
from app.agents.planner import planner_agent
from app.agents.executor import executor_agent
from app.agents.evaluator import evaluator_agent

from app.tools.browser import browser_use_tool
from app.types.output import UserQueryPlan

custom_client = AsyncOpenAI(base_url=BASIC_LLM_URL api_key=BASIC_LLM_URL)
set_default_openai_client(client=custom_client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)


agent = Agent(name="Assistant", model="deepseek-chat", instructions="你是一个可以和浏览器交互的助手，请根据用户的问题，使用浏览器交互。", tools=[browser_use_tool])


async def main():
#     config = BrowserContextConfig(
#     cookies_file="/Users/admin/work/cookies.json",
#     wait_for_network_idle_page_load_time=60.0,
#     browser_window_size={'width': 1280, 'height': 1100},
#     locale='en-US',
#     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
#     highlight_elements=True,
#     viewport_expansion=500,
# )
#     browser = Browser()
#     context = BrowserContext(browser=browser, config=config)


#     llm = ChatOpenAI(base_url=BASIC_LLM_URL, model='deepseek-chat', api_key=SecretStr(BASIC_LLM_API_KEY))
#     agent = BrowserAgent(
#         task="打开小红书,搜索人工智能,打开第五个帖子,然后返回帖子内容",
#         llm=llm,
#         use_vision=False,
#         browser_context=context,
#     )
#     result = await agent.run()
#     print('#####')
#     print(result.final_result())


    result = await Runner.run(starting_agent=planner_agent, input="用户目标:获取最新的大模型ai agent博客,挑选3篇,然后总结,然后写一篇摘要;请你制定一个简易的计划")
    print(result.final_output_as(UserQueryPlan))

    # try:
    #     await file_mcp_server.connect()  
    #     message = "write ”hello world” to the file demo.txt"
    #     print(f"Running: {message}")
    #     agent_mcp = Agent(
    #         name="Assistant",
    #         model="deepseek-chat",
    #         instructions="Use the tools to read the filesystem and answer questions based on those files.",
    #         mcp_servers=[file_mcp_server],
    #     )
    #     result = await Runner.run(starting_agent=agent_mcp, input=message)
    #     print(result.final_output)
    # finally:
    #     await file_mcp_server.cleanup()





import asyncio
asyncio.run(main())

