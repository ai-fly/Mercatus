import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = Field(default="Mercatus", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    max_runtime_hours: int = Field(default=8, description="每日最大运行时长（小时）")
    
    # LLM配置
    base_model_name: Optional[str] = Field(default=None, description="基础模型名称")
    basic_llm_url: Optional[str] = Field(default=None, description="基础LLM API URL")
    basic_llm_api_key: Optional[str] = Field(default=None, description="基础LLM API密钥")
    google_api_key: Optional[str] = Field(default=None, description="Google API密钥")
    
    # 搜索配置
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily搜索API密钥")
    
    # 平台配置
    twitter_api_key: Optional[str] = Field(default=None, description="Twitter API密钥")
    facebook_api_key: Optional[str] = Field(default=None, description="Facebook API密钥")
    reddit_client_id: Optional[str] = Field(default=None, description="Reddit客户端ID")
    reddit_client_secret: Optional[str] = Field(default=None, description="Reddit客户端密钥")
    lemon8_api_key: Optional[str] = Field(default=None, description="Lemon8 API密钥")
    
    # 缓存配置
    redis_url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")

    # 消息队列配置
    rocketmq_name_server: str = Field(default="localhost:9876", description="RocketMQ名称服务器")
    rocketmq_topic_prefix: str = Field(default="mercatus", description="RocketMQ主题前缀")
    
    # VNC和浏览器隔离配置
    vnc_base_port: int = Field(default=5900, description="VNC基础端口")
    vnc_password: Optional[str] = Field(default=None, description="VNC密码")
    browser_timeout: int = Field(default=300, description="浏览器超时时间（秒）")
    max_concurrent_browsers: int = Field(default=10, description="最大并发浏览器数量")
    
    # 政策更新配置
    policy_update_interval: int = Field(default=86400, description="政策更新间隔（秒），默认24小时")
    policy_config_file: str = Field(default="config/platform_policies.yaml", description="平台政策配置文件路径")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 全局配置实例
settings = Config()

# 向后兼容的变量（保持原有代码可用）
BASE_MODEL_NAME = settings.base_model_name
BASIC_LLM_URL = settings.basic_llm_url
BASIC_LLM_API_KEY = settings.basic_llm_api_key
GOOGLE_API_KEY = settings.google_api_key
TAVILY_API_KEY = settings.tavily_api_key
