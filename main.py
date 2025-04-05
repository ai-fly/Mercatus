import os
import logging
from agents import Agent, Runner, set_default_openai_api, set_tracing_disabled
from browser_use import Agent as BrowserAgent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContext
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from agents import set_default_openai_client
from pydantic import SecretStr
from app.config import BASIC_LLM_API_KEY, BASIC_LLM_URL
from app.mcps.file import file_mcp_server
from app.tools.file import file_tool
from agents.mcp import MCPServer, MCPServerStdio
from app.agents.planner import planner_agent
from app.agents.executor import executor_agent
from app.agents.evaluator import evaluator_agent
from app.manager import Manager
from app.tools.browser import browser_use_tool
from app.types.output import UserQueryPlan
from app.utils.logging import setup_logger

# Set up main logger
logger = setup_logger(name="main")

custom_client = AsyncOpenAI(base_url=BASIC_LLM_URL, api_key=BASIC_LLM_API_KEY)
set_default_openai_client(client=custom_client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

async def main():

    try:
        logger.info("Initializing file MCP server")
        await file_mcp_server.connect()
        logger.info("File MCP server connected successfully")
          
        logger.info("Initializing manager")
        manager = Manager()
        
        query = "Search for the latest information on deepseek and save it to a file."
        logger.info(f"Executing query: {query}")
        
        result = await manager.run(query)

        logger.debug(f"Final result: {result}")
        print(result)
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
    finally:
        logger.info("Cleaning up resources...")
        await file_mcp_server.cleanup()



import asyncio
if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(main())
    logger.info("Application ended")

