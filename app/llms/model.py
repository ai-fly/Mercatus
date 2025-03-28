
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from app.config import BASIC_LLM_URL, BASIC_LLM_API_KEY



def get_llm():
    """
    get the llm model instance
    
    Returns:
        ChatOpenAI: the llm model instance
    """
    return ChatOpenAI(base_url=BASIC_LLM_URL, model='deepseek-chat', api_key=SecretStr(BASIC_LLM_API_KEY))


