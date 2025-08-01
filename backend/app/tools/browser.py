import uuid
from browser_use import Agent as BrowserAgent, Browser, BrowserConfig
from langchain_core.tools import tool
from app.llms.model import get_vertex_model


BROWSER_HISTORY_DIR = "artifacts/browser_history"

# Basic configuration
config = BrowserConfig(
    headless=False,
    disable_security=True
)

# Initialize browser
browser = Browser(config=config)


@tool
async def browser_use_tool(instruction: str) -> str:
    """Use this tool to interact with the browser, such as opening a specific webpage or performing operations within a webpage, including but not limited to collecting data from the internet, searching for information, or accessing designated web pages.

    Args:
        instruction: The instruction to interact with the browser.
    """

    generated_gif_path = f"{BROWSER_HISTORY_DIR}/{uuid.uuid4()}.gif"
    agent = BrowserAgent(
        task=instruction,
        llm=get_vertex_model(),
        browser=browser,
        generate_gif=generated_gif_path,
        use_vision=False,
    )
    result = await agent.run()
    return result.final_result()
