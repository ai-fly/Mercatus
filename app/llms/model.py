
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from app.config import BASE_MODEL_NAME, BASIC_LLM_URL, BASIC_LLM_API_KEY



def get_llm():
    """
    get the llm model instance
    
    Returns:
        ChatOpenAI: the llm model instance
    """
    return ChatOpenAI(base_url=BASIC_LLM_URL, model=BASE_MODEL_NAME, api_key=SecretStr(BASIC_LLM_API_KEY))



def get_vertex_model(model_name="gemini-2.5-pro"):
    return ChatVertexAI(model_name=model_name, project="contraprise-443714", location="global")