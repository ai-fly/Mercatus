import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from app.config import BASE_MODEL_NAME, BASIC_LLM_URL, BASIC_LLM_API_KEY, GOOGLE_API_KEY

def get_llm():
    """
    get the llm model instance
    
    Returns:
        ChatOpenAI: the llm model instance
    """
    return ChatOpenAI(base_url=BASIC_LLM_URL, model=BASE_MODEL_NAME, api_key=SecretStr(BASIC_LLM_API_KEY))


def get_vertex_model(model_name="gemini-2.5-pro"):
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=SecretStr(GOOGLE_API_KEY)
    )
