# Mercatus 配置文档

## 配置概述

Mercatus 使用 Pydantic BaseSettings 进行配置管理，支持从环境变量和 `.env` 文件加载配置。配置按功能模块分组，提供类型安全和验证。

## 配置文件结构

### 1. 应用基础配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `APP_NAME` | str | "Mercatus" | 应用名称 |
| `DEBUG` | bool | false | 调试模式 |
| `LOG_LEVEL` | LogLevel | INFO | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `MAX_RUNTIME_HOURS` | int | 8 | 每日最大运行时长（小时） |

### 2. LLM配置

#### 基础配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `BASE_MODEL_NAME` | str | None | 基础模型名称 |
| `BASIC_LLM_URL` | str | None | 基础LLM API URL |
| `BASIC_LLM_API_KEY` | str | None | 基础LLM API密钥 |
| `GOOGLE_API_KEY` | str | None | Google API密钥 |

#### 高级配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `LLM_TEMPERATURE` | float | 0.7 | LLM温度参数 (0-2) |
| `LLM_MAX_TOKENS` | int | 2048 | LLM最大token数 |
| `LLM_TIMEOUT` | int | 60 | LLM请求超时时间（秒） |
| `LLM_RETRY_ATTEMPTS` | int | 3 | LLM重试次数 |

### 3. 搜索配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `TAVILY_API_KEY` | str | None | Tavily搜索API密钥 |
| `SEARCH_TIMEOUT` | int | 30 | 搜索超时时间（秒） |
| `SEARCH_MAX_RESULTS` | int | 10 | 搜索最大结果数 |

### 4. 平台API配置

#### Twitter配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `TWITTER_API_KEY` | str | None | Twitter API密钥 |
| `TWITTER_API_SECRET` | str | None | Twitter API密钥 |
| `TWITTER_ACCESS_TOKEN` | str | None | Twitter访问令牌 |
| `TWITTER_ACCESS_TOKEN_SECRET` | str | None | Twitter访问令牌密钥 |

#### Facebook配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `FACEBOOK_API_KEY` | str | None | Facebook API密钥 |
| `FACEBOOK_APP_ID` | str | None | Facebook应用ID |
| `FACEBOOK_APP_SECRET` | str | None | Facebook应用密钥 |

#### Reddit配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDDIT_CLIENT_ID` | str | None | Reddit客户端ID |
| `REDDIT_CLIENT_SECRET` | str | None | Reddit客户端密钥 |
| `REDDIT_USER_AGENT` | str | "Mercatus:v1.0.0" | Reddit用户代理 |

#### Lemon8配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `LEMON8_API_KEY` | str | None | Lemon8 API密钥 |
| `LEMON8_APP_ID` | str | None | Lemon8应用ID |

### 5. 缓存配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDIS_URL` | str | "redis://localhost:6379" | Redis连接URL |
| `REDIS_PASSWORD` | str | None | Redis密码 |
| `REDIS_DB` | int | 0 | Redis数据库索引 |
| `REDIS_MAX_CONNECTIONS` | int | 20 | Redis最大连接数 |
| `REDIS_TIMEOUT` | int | 5 | Redis连接超时时间（秒） |
| `CACHE_TTL` | int | 3600 | 缓存TTL（秒） |
| `CACHE_PREFIX` | str | "mercatus" | 缓存键前缀 |

### 6. 消息队列配置

#### RocketMQ基础配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ROCKETMQ_NAME_SERVER` | str | "localhost:9876" | RocketMQ名称服务器 |
| `ROCKETMQ_TOPIC_PREFIX` | str | "mercatus" | RocketMQ主题前缀 |
| `ROCKETMQ_PRODUCER_GROUP` | str | "mercatus_producer" | RocketMQ生产者组 |
| `ROCKETMQ_CONSUMER_GROUP` | str | "mercatus_consumer" | RocketMQ消费者组 |

#### 队列主题配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `JEFF_QUEUE_TOPIC` | str | "mercatus_jeff" | Jeff专家队列主题 |
| `MONICA_QUEUE_TOPIC` | str | "mercatus_monica" | Monica专家队列主题 |
| `HENRY_QUEUE_TOPIC` | str | "mercatus_henry" | Henry专家队列主题 |

#### 消息队列高级配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `MESSAGE_MAX_RETRY` | int | 3 | 消息最大重试次数 |
| `MESSAGE_TIMEOUT` | int | 300 | 消息处理超时时间（秒） |
| `QUEUE_BATCH_SIZE` | int | 10 | 队列批量处理大小 |

### 7. VNC和浏览器隔离配置

#### VNC配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `VNC_BASE_PORT` | int | 5900 | VNC基础端口 |
| `VNC_PASSWORD` | str | None | VNC密码 |
| `VNC_DISPLAY_WIDTH` | int | 1920 | VNC显示宽度 |
| `VNC_DISPLAY_HEIGHT` | int | 1080 | VNC显示高度 |

#### 浏览器配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `BROWSER_TIMEOUT` | int | 300 | 浏览器超时时间（秒） |
| `MAX_CONCURRENT_BROWSERS` | int | 10 | 最大并发浏览器数量 |
| `BROWSER_HEADLESS` | bool | false | 浏览器无头模式 |
| `BROWSER_USER_DATA_DIR` | str | "/tmp/mercatus_browser" | 浏览器用户数据目录 |

#### 用户隔离配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `USER_ISOLATION_ENABLED` | bool | true | 启用用户隔离 |
| `MAX_USERS_PER_INSTANCE` | int | 50 | 每个实例最大用户数 |
| `USER_SESSION_TIMEOUT` | int | 7200 | 用户会话超时时间（秒） |

### 8. 政策更新配置

#### 基础配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `POLICY_UPDATE_INTERVAL` | int | 86400 | 政策更新间隔（秒），默认24小时 |
| `POLICY_CONFIG_FILE` | str | "config/platform_policies.yaml" | 平台政策配置文件路径 |
| `POLICY_CACHE_TTL` | int | 3600 | 政策缓存TTL（秒） |
| `POLICY_UPDATE_ENABLED` | bool | true | 启用政策自动更新 |

#### 政策爬虫配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `POLICY_CRAWLER_TIMEOUT` | int | 60 | 政策爬虫超时时间（秒） |
| `POLICY_CRAWLER_RETRY` | int | 3 | 政策爬虫重试次数 |
| `POLICY_CRAWLER_USER_AGENT` | str | "Mozilla/5.0..." | 政策爬虫用户代理 |

### 9. 数据库配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | str | None | 数据库连接URL |
| `DATABASE_POOL_SIZE` | int | 10 | 数据库连接池大小 |
| `DATABASE_MAX_OVERFLOW` | int | 20 | 数据库连接池最大溢出 |
| `DATABASE_TIMEOUT` | int | 30 | 数据库连接超时时间（秒） |

### 10. 文件存储配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `FILE_STORAGE_PATH` | str | "./storage" | 文件存储路径 |
| `MAX_FILE_SIZE` | int | 10485760 | 最大文件大小（字节） |
| `ALLOWED_FILE_TYPES` | List[str] | ["jpg", "jpeg", "png", "gif", "mp4", "avi", "mov"] | 允许的文件类型 |

### 11. 监控和日志配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ENABLE_METRICS` | bool | true | 启用指标监控 |
| `METRICS_PORT` | int | 8080 | 指标端口 |
| `LOG_FILE_PATH` | str | "./logs/mercatus.log" | 日志文件路径 |
| `LOG_ROTATION_SIZE` | str | "100MB" | 日志轮转大小 |
| `LOG_RETENTION_DAYS` | int | 30 | 日志保留天数 |

### 12. 安全配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `SECRET_KEY` | str | "your-secret-key-change-in-production" | 应用密钥 |
| `JWT_SECRET` | str | "your-jwt-secret-change-in-production" | JWT密钥 |
| `JWT_EXPIRATION` | int | 3600 | JWT过期时间（秒） |

#### API限流配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `RATE_LIMIT_ENABLED` | bool | true | 启用API限流 |
| `RATE_LIMIT_PER_MINUTE` | int | 100 | 每分钟请求限制 |
| `RATE_LIMIT_BURST` | int | 20 | 突发请求限制 |

### 13. 内容生成配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `CONTENT_MAX_LENGTH` | int | 2000 | 内容最大长度 |
| `CONTENT_GENERATION_TIMEOUT` | int | 120 | 内容生成超时时间（秒） |
| `CONTENT_QUALITY_THRESHOLD` | float | 0.8 | 内容质量阈值 (0-1) |

#### 平台特定配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `TWITTER_MAX_LENGTH` | int | 280 | Twitter最大字符数 |
| `FACEBOOK_MAX_LENGTH` | int | 5000 | Facebook最大字符数 |
| `REDDIT_MAX_LENGTH` | int | 10000 | Reddit最大字符数 |
| `LEMON8_MAX_LENGTH` | int | 2000 | Lemon8最大字符数 |

### 14. 合规检查配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `COMPLIANCE_ENABLED` | bool | true | 启用合规检查 |
| `COMPLIANCE_TIMEOUT` | int | 30 | 合规检查超时时间（秒） |
| `COMPLIANCE_RETRY_ATTEMPTS` | int | 3 | 合规检查重试次数 |

#### 地区合规配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEFAULT_REGION` | Region | "us" | 默认地区 |
| `SUPPORTED_REGIONS` | List[Region] | ["china", "us", "uk", "eu", "vietnam", "uae", "russia"] | 支持的地区列表 |

### 15. 任务调度配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `SCHEDULER_ENABLED` | bool | true | 启用任务调度器 |
| `SCHEDULER_MAX_WORKERS` | int | 4 | 调度器最大工作线程数 |
| `TASK_TIMEOUT` | int | 600 | 任务超时时间（秒） |
| `TASK_RETRY_DELAY` | int | 60 | 任务重试延迟（秒） |

## 枚举类型

### LogLevel
- `DEBUG`: 调试级别
- `INFO`: 信息级别
- `WARNING`: 警告级别
- `ERROR`: 错误级别
- `CRITICAL`: 严重错误级别

### Platform
- `TWITTER`: Twitter平台
- `FACEBOOK`: Facebook平台
- `REDDIT`: Reddit平台
- `LEMON8`: Lemon8平台

### ContentType
- `TEXT`: 纯文本内容
- `TEXT_IMAGE`: 图文内容
- `VIDEO`: 视频内容

### Region
- `CHINA`: 中国
- `US`: 美国
- `UK`: 英国
- `EU`: 欧盟
- `VIETNAM`: 越南
- `UAE`: 阿联酋
- `RUSSIA`: 俄罗斯

### AgentRole
- `JEFF`: 营销策划专家
- `MONICA`: 内容生成专家
- `HENRY`: 内容审查专家

## 配置方法

### 1. 使用配置实例
```python
from app.config import settings

# 访问配置
print(settings.app_name)
print(settings.llm_temperature)
print(settings.redis_url)
```

### 2. 使用辅助方法
```python
from app.config import settings, Platform, AgentRole

# 获取平台配置
twitter_config = settings.get_platform_config(Platform.TWITTER)

# 获取智能体队列主题
jeff_topic = settings.get_agent_queue_topic(AgentRole.JEFF)

# 检查平台是否已配置
is_configured = settings.is_platform_configured(Platform.TWITTER)
```

### 3. 使用向后兼容变量
```python
from app.config import BASE_MODEL_NAME, TAVILY_API_KEY
```

## 配置验证

配置类包含以下验证器：

- `log_level`: 确保日志级别有效
- `max_runtime_hours`: 确保运行时长在1-24小时之间
- `llm_temperature`: 确保温度参数在0-2之间
- `content_quality_threshold`: 确保质量阈值在0-1之间

## 环境变量文件

创建 `.env` 文件并设置相应的环境变量。参考 `.env.example` 文件获取完整的配置示例。

## 生产环境注意事项

1. **安全密钥**: 在生产环境中必须更改 `SECRET_KEY` 和 `JWT_SECRET`
2. **数据库连接**: 配置生产环境的数据库连接URL
3. **Redis配置**: 配置生产环境的Redis连接和密码
4. **API密钥**: 确保所有平台API密钥正确配置
5. **日志级别**: 生产环境建议使用 `INFO` 或 `WARNING` 级别
6. **调试模式**: 生产环境必须设置 `DEBUG=false` 