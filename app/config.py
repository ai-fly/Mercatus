import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv
from enum import Enum

# 加载环境变量
load_dotenv()

class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Platform(str, Enum):
    """支持的平台枚举"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    REDDIT = "reddit"
    LEMON8 = "lemon8"

class ContentType(str, Enum):
    """内容类型枚举"""
    TEXT = "text"
    TEXT_IMAGE = "text_image"
    VIDEO = "video"

class Region(str, Enum):
    """地区枚举"""
    CHINA = "china"
    US = "us"
    UK = "uk"
    EU = "eu"
    VIETNAM = "vietnam"
    UAE = "uae"
    RUSSIA = "russia"

class AgentRole(str, Enum):
    """智能体角色枚举"""
    JEFF = "jeff"  # 营销策划专家
    MONICA = "monica"  # 内容生成专家
    HENRY = "henry"  # 内容审查专家

class Config(BaseSettings):
    """Mercatus应用配置"""
    
    # ========== 应用基础配置 ==========
    app_name: str = Field(default="Mercatus", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    max_runtime_hours: int = Field(default=8, description="每日最大运行时长（小时）")
    
    # ========== LLM配置 ==========
    base_model_name: Optional[str] = Field(default=None, description="基础模型名称")
    basic_llm_url: Optional[str] = Field(default=None, description="基础LLM API URL")
    basic_llm_api_key: Optional[str] = Field(default=None, description="基础LLM API密钥")
    google_api_key: Optional[str] = Field(default=None, description="Google API密钥")
    
    # LLM高级配置
    llm_temperature: float = Field(default=0.7, description="LLM温度参数")
    llm_max_tokens: int = Field(default=2048, description="LLM最大token数")
    llm_timeout: int = Field(default=60, description="LLM请求超时时间（秒）")
    llm_retry_attempts: int = Field(default=3, description="LLM重试次数")
    
    # ========== 搜索配置 ==========
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily搜索API密钥")
    search_timeout: int = Field(default=30, description="搜索超时时间（秒）")
    search_max_results: int = Field(default=10, description="搜索最大结果数")
    
    # ========== 平台API配置 ==========
    # Twitter配置
    twitter_api_key: Optional[str] = Field(default=None, description="Twitter API密钥")
    twitter_api_secret: Optional[str] = Field(default=None, description="Twitter API密钥")
    twitter_access_token: Optional[str] = Field(default=None, description="Twitter访问令牌")
    twitter_access_token_secret: Optional[str] = Field(default=None, description="Twitter访问令牌密钥")
    
    # Facebook配置
    facebook_api_key: Optional[str] = Field(default=None, description="Facebook API密钥")
    facebook_app_id: Optional[str] = Field(default=None, description="Facebook应用ID")
    facebook_app_secret: Optional[str] = Field(default=None, description="Facebook应用密钥")
    
    # Reddit配置
    reddit_client_id: Optional[str] = Field(default=None, description="Reddit客户端ID")
    reddit_client_secret: Optional[str] = Field(default=None, description="Reddit客户端密钥")
    reddit_user_agent: str = Field(default="Mercatus:v1.0.0", description="Reddit用户代理")
    
    # Lemon8配置
    lemon8_api_key: Optional[str] = Field(default=None, description="Lemon8 API密钥")
    lemon8_app_id: Optional[str] = Field(default=None, description="Lemon8应用ID")
    
    # ========== 缓存配置 ==========
    redis_url: str = Field(default="redis://localhost:6379", description="Redis连接URL")
    redis_password: Optional[str] = Field(default=None, description="Redis密码")
    redis_db: int = Field(default=0, description="Redis数据库索引")
    redis_max_connections: int = Field(default=20, description="Redis最大连接数")
    redis_timeout: int = Field(default=5, description="Redis连接超时时间（秒）")
    
    # 缓存策略
    cache_ttl: int = Field(default=3600, description="缓存TTL（秒）")
    cache_prefix: str = Field(default="mercatus", description="缓存键前缀")
    
    # ========== 消息队列配置 ==========
    rocketmq_name_server: str = Field(default="localhost:9876", description="RocketMQ名称服务器")
    rocketmq_topic_prefix: str = Field(default="mercatus", description="RocketMQ主题前缀")
    rocketmq_producer_group: str = Field(default="mercatus_producer", description="RocketMQ生产者组")
    rocketmq_consumer_group: str = Field(default="mercatus_consumer", description="RocketMQ消费者组")
    
    # 队列主题配置
    jeff_queue_topic: str = Field(default="mercatus_jeff", description="Jeff专家队列主题")
    monica_queue_topic: str = Field(default="mercatus_monica", description="Monica专家队列主题")
    henry_queue_topic: str = Field(default="mercatus_henry", description="Henry专家队列主题")
    
    # 消息队列高级配置
    message_max_retry: int = Field(default=3, description="消息最大重试次数")
    message_timeout: int = Field(default=300, description="消息处理超时时间（秒）")
    queue_batch_size: int = Field(default=10, description="队列批量处理大小")
    
    # ========== VNC和浏览器隔离配置 ==========
    vnc_base_port: int = Field(default=5900, description="VNC基础端口")
    vnc_password: Optional[str] = Field(default=None, description="VNC密码")
    vnc_display_width: int = Field(default=1920, description="VNC显示宽度")
    vnc_display_height: int = Field(default=1080, description="VNC显示高度")
    
    browser_timeout: int = Field(default=300, description="浏览器超时时间（秒）")
    max_concurrent_browsers: int = Field(default=10, description="最大并发浏览器数量")
    browser_headless: bool = Field(default=False, description="浏览器无头模式")
    browser_user_data_dir: str = Field(default="/tmp/mercatus_browser", description="浏览器用户数据目录")
    
    # 用户隔离配置
    user_isolation_enabled: bool = Field(default=True, description="启用用户隔离")
    max_users_per_instance: int = Field(default=50, description="每个实例最大用户数")
    user_session_timeout: int = Field(default=7200, description="用户会话超时时间（秒）")
    
    # ========== 政策更新配置 ==========
    policy_update_interval: int = Field(default=86400, description="政策更新间隔（秒），默认24小时")
    policy_config_file: str = Field(default="config/platform_policies.yaml", description="平台政策配置文件路径")
    policy_cache_ttl: int = Field(default=3600, description="政策缓存TTL（秒）")
    policy_update_enabled: bool = Field(default=True, description="启用政策自动更新")
    
    # 政策爬虫配置
    policy_crawler_timeout: int = Field(default=60, description="政策爬虫超时时间（秒）")
    policy_crawler_retry: int = Field(default=3, description="政策爬虫重试次数")
    policy_crawler_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="政策爬虫用户代理"
    )
    
    # ========== 数据库配置 ==========
    database_url: Optional[str] = Field(default=None, description="数据库连接URL")
    database_pool_size: int = Field(default=10, description="数据库连接池大小")
    database_max_overflow: int = Field(default=20, description="数据库连接池最大溢出")
    database_timeout: int = Field(default=30, description="数据库连接超时时间（秒）")
    
    # ========== 文件存储配置 ==========
    file_storage_path: str = Field(default="./storage", description="文件存储路径")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小（字节）")
    allowed_file_types: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "mp4", "avi", "mov"],
        description="允许的文件类型"
    )
    
    # ========== 监控和日志配置 ==========
    enable_metrics: bool = Field(default=True, description="启用指标监控")
    metrics_port: int = Field(default=8080, description="指标端口")
    log_file_path: str = Field(default="./logs/mercatus.log", description="日志文件路径")
    log_rotation_size: str = Field(default="100MB", description="日志轮转大小")
    log_retention_days: int = Field(default=30, description="日志保留天数")
    
    # ========== 安全配置 ==========
    secret_key: str = Field(default="your-secret-key-change-in-production", description="应用密钥")
    jwt_secret: str = Field(default="your-jwt-secret-change-in-production", description="JWT密钥")
    jwt_expiration: int = Field(default=3600, description="JWT过期时间（秒）")
    
    # API限流配置
    rate_limit_enabled: bool = Field(default=True, description="启用API限流")
    rate_limit_per_minute: int = Field(default=100, description="每分钟请求限制")
    rate_limit_burst: int = Field(default=20, description="突发请求限制")
    
    # ========== 内容生成配置 ==========
    content_max_length: int = Field(default=2000, description="内容最大长度")
    content_generation_timeout: int = Field(default=120, description="内容生成超时时间（秒）")
    content_quality_threshold: float = Field(default=0.8, description="内容质量阈值")
    
    # 平台特定配置
    twitter_max_length: int = Field(default=280, description="Twitter最大字符数")
    facebook_max_length: int = Field(default=5000, description="Facebook最大字符数")
    reddit_max_length: int = Field(default=10000, description="Reddit最大字符数")
    lemon8_max_length: int = Field(default=2000, description="Lemon8最大字符数")
    
    # ========== 合规检查配置 ==========
    compliance_enabled: bool = Field(default=True, description="启用合规检查")
    compliance_timeout: int = Field(default=30, description="合规检查超时时间（秒）")
    compliance_retry_attempts: int = Field(default=3, description="合规检查重试次数")
    
    # 地区合规配置
    default_region: Region = Field(default=Region.US, description="默认地区")
    supported_regions: List[Region] = Field(
        default=[Region.CHINA, Region.US, Region.UK, Region.EU, Region.VIETNAM, Region.UAE, Region.RUSSIA],
        description="支持的地区列表"
    )
    
    # ========== 任务调度配置 ==========
    scheduler_enabled: bool = Field(default=True, description="启用任务调度器")
    scheduler_max_workers: int = Field(default=4, description="调度器最大工作线程数")
    task_timeout: int = Field(default=600, description="任务超时时间（秒）")
    task_retry_delay: int = Field(default=60, description="任务重试延迟（秒）")
    
    # ========== 验证器 ==========
    @validator('log_level')
    def validate_log_level(cls, v):
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v
    
    @validator('max_runtime_hours')
    def validate_max_runtime_hours(cls, v):
        if v <= 0 or v > 24:
            raise ValueError('max_runtime_hours must be between 1 and 24')
        return v
    
    @validator('llm_temperature')
    def validate_llm_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('llm_temperature must be between 0 and 2')
        return v
    
    @validator('content_quality_threshold')
    def validate_content_quality_threshold(cls, v):
        if v < 0 or v > 1:
            raise ValueError('content_quality_threshold must be between 0 and 1')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        use_enum_values = True
    
    def get_platform_config(self, platform: Platform) -> Dict[str, Any]:
        """获取平台特定配置"""
        platform_configs = {
            Platform.TWITTER: {
                'api_key': self.twitter_api_key,
                'api_secret': self.twitter_api_secret,
                'access_token': self.twitter_access_token,
                'access_token_secret': self.twitter_access_token_secret,
                'max_length': self.twitter_max_length,
            },
            Platform.FACEBOOK: {
                'api_key': self.facebook_api_key,
                'app_id': self.facebook_app_id,
                'app_secret': self.facebook_app_secret,
                'max_length': self.facebook_max_length,
            },
            Platform.REDDIT: {
                'client_id': self.reddit_client_id,
                'client_secret': self.reddit_client_secret,
                'user_agent': self.reddit_user_agent,
                'max_length': self.reddit_max_length,
            },
            Platform.LEMON8: {
                'api_key': self.lemon8_api_key,
                'app_id': self.lemon8_app_id,
                'max_length': self.lemon8_max_length,
            }
        }
        return platform_configs.get(platform, {})
    
    def get_agent_queue_topic(self, agent: AgentRole) -> str:
        """获取智能体队列主题"""
        topics = {
            AgentRole.JEFF: self.jeff_queue_topic,
            AgentRole.MONICA: self.monica_queue_topic,
            AgentRole.HENRY: self.henry_queue_topic,
        }
        return topics.get(agent, f"{self.rocketmq_topic_prefix}_{agent}")
    
    def is_platform_configured(self, platform: Platform) -> bool:
        """检查平台是否已配置"""
        config = self.get_platform_config(platform)
        required_keys = {
            Platform.TWITTER: ['api_key', 'api_secret'],
            Platform.FACEBOOK: ['api_key', 'app_id'],
            Platform.REDDIT: ['client_id', 'client_secret'],
            Platform.LEMON8: ['api_key'],
        }
        
        required = required_keys.get(platform, [])
        return all(config.get(key) for key in required)

# 全局配置实例
settings = Config()

# 向后兼容的变量（保持原有代码可用）
BASE_MODEL_NAME = settings.base_model_name
BASIC_LLM_URL = settings.basic_llm_url
BASIC_LLM_API_KEY = settings.basic_llm_api_key
GOOGLE_API_KEY = settings.google_api_key
TAVILY_API_KEY = settings.tavily_api_key

# 导出常用枚举和配置
__all__ = [
    'Config',
    'settings',
    'LogLevel',
    'Platform',
    'ContentType',
    'Region',
    'AgentRole',
    'BASE_MODEL_NAME',
    'BASIC_LLM_URL',
    'BASIC_LLM_API_KEY',
    'GOOGLE_API_KEY',
    'TAVILY_API_KEY',
]
