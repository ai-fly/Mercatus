# Mercatus 项目规划文档

## 项目概述

Mercatus 是一个基于多智能体（Multi-Agent）的内容工厂系统，作为**Agent Workload**组件，专注于提供营销内容的智能生成和审核服务。本项目是完整Mercatus应用架构中的核心组件之一。

### 项目定位
- **组件角色**：Agent Workload层，负责核心的营销策略、内容生成和审核功能
- **服务特性**：重服务特性，需要独立部署和管理
- **隔离要求**：每个用户的VNC和浏览器环境完全隔离
- **技术栈**：Python 3.12+、LangGraph、消息队列、VNC服务器

## 完整应用架构

### 四大核心组件
1. **PC前端页面**：用户界面和交互
2. **Mercatus-API**：Web服务和任务调度
3. **Mercatus (本项目)**：Agent核心和内容生成
4. **Mercatus-Client**：客户端内容发布

### 系统交互流程
需求输入 → API处理 → 内容生成 → 内容审核 → 内容发布 → 数据回传 → 结果展示

## 核心智能体架构

### 三大专家角色

#### 1. 营销策划专家 Jeff (Marketing Strategy Expert)
**职责**：
- 制定全面的营销策略
- 目标设定和市场定位
- 平台策略制定
- 渠道策略规划
- 预算规划与资源分配

**核心能力**：
- 目标设定（品牌认知、用户获取、客户留存、销售转化、用户活跃）
- 渠道策略（内容营销、SEO/SEM、社交媒体、电邮营销、KOL营销、联盟营销、付费广告）
- 数据追踪与效果评估
- 迭代优化机制

#### 2. 内容生成专家 Monica (Content Generation Expert)
**职责**：
- 根据营销策略执行内容创作
- 多平台内容适配
- 运用各种内容营销技巧
- 生成指定类型的内容

**核心能力**：
- 平台内容适配（X/Twitter、Facebook、Reddit、Lemon8）
- 内容营销技巧（情境策略、内容结构、心理驱动、搜索优化、创意互动、权威建设）
- 多种内容类型生成（文字、图文、视频）

#### 3. 内容审查专家 Henry (Content Review Expert)
**职责**：
- 确保内容符合平台政策
- 地区法规合规性检查
- 内容质量评估
- 政策实时更新管理

**核心能力**：
- 平台合规要求（X/Twitter、Facebook、Reddit、Lemon8）
- 地区法规要求（中国、美国、英国/欧盟、越南、阿联酋、俄罗斯）
- 政策实时更新系统
- 审核决策和反馈机制

## 目录结构设计

### 核心目录架构
```
app/
├── agents/           # 智能体核心逻辑
│   ├── planner.py   # Jeff - 营销策划专家
│   ├── executor.py  # Monica - 内容生成专家
│   ├── evaluator.py # Henry - 内容审查专家
│   └── state.py     # 状态管理
├── llms/            # 大语言模型集成
│   └── model.py     # LLM调用和响应处理
├── tools/           # 工具集合
│   ├── browser.py   # 浏览器操作工具
│   ├── file.py      # 文件操作工具
│   └── search.py    # 搜索工具
├── prompts/         # 提示词模板
│   ├── planner.py   # Jeff的提示词
│   ├── executor.py  # Monica的提示词
│   └── evaluator.py # Henry的提示词
├── types/           # 类型定义
│   ├── context.py   # 上下文类型
│   └── output.py    # 输出类型
├── utils/           # 工具函数
│   └── logging.py   # 日志管理
├── mcps/            # MCP服务器定义
│   └── mcp_entrypoint.py
├── controllers/     # 控制器层
├── core/            # 核心业务逻辑
├── config.py        # 配置管理
└── manager.py       # 管理器
```

### 专家模块设计原则
- **单一职责**：每个专家专注于自己的核心能力
- **松耦合**：通过消息队列进行异步通信
- **可扩展**：支持新增专家和能力模块
- **状态管理**：实时跟踪各专家工作状态

## 技术架构设计

### 消息队列系统
- **异步通信**：专家间非阻塞式消息传递
- **状态同步**：实时更新各专家工作状态
- **失败重试**：自动重试机制和失败处理
- **消息持久化**：确保消息不丢失
- **优先级队列**：支持任务优先级管理

### 隔离系统设计
- **用户隔离**：每个用户独立的运行环境
- **浏览器隔离**：独立的VNC和浏览器实例
- **数据隔离**：用户数据完全隔离存储
- **进程隔离**：独立的进程空间和资源管理
- **平台隔离**：每个用户的平台账户独立管理

### 政策更新系统
- **定时任务**：每日定时执行政策更新任务
- **智能爬虫**：自动识别和提取政策变更内容
- **差异检测**：智能比较政策变化并标记重要更新
- **规则引擎**：自动将政策变化转换为合规检查规则
- **通知机制**：及时通知相关专家和用户政策变化

## 平台管理架构

### 支持平台
- **X (Twitter)**：社交媒体平台
- **Facebook**：社交网络平台
- **Reddit**：社区讨论平台
- **Lemon8**：生活方式分享平台

### 内容类型支持
- **文字内容**：纯文本帖子、推文、评论
- **文字+图片**：图文结合的社交媒体内容
- **视频内容**：短视频、宣传视频、教程视频

### 平台配置管理
```yaml
platform_policies:
  twitter:
    url: "https://help.twitter.com/en/rules-and-policies"
    content_policy: "https://help.twitter.com/en/rules-and-policies/twitter-rules"
    advertising_policy: "https://business.twitter.com/en/help/ads-policies.html"
  # ... 其他平台配置
```

## 开发规范与标准

### 代码规范
- **PEP 8**：严格遵循Python编码标准
- **类型提示**：所有函数参数和返回值使用类型提示
- **函数式编程**：优先使用函数式编程模式，避免不必要的类
- **描述性命名**：使用清晰的变量名（如`is_valid`、`has_appointments`、`should_schedule`）
- **模块结构**：imports、constants、functions、classes、main execution

### 命名约定
- **变量/函数/模块**：snake_case
- **类名**：PascalCase
- **常量**：UPPER_CASE
- **目录**：小写加下划线（如`medical_providers`、`appointment_scheduler`）

### 函数和类设计
- **纯函数**：尽可能编写纯函数
- **数据结构**：使用dataclasses或Pydantic模型
- **单一职责**：实现单一职责原则
- **提前返回**：使用提前返回和守卫子句
- **函数长度**：尽可能保持函数在50行以内

### 错误处理和验证
- **优先错误处理**：及早处理错误和边缘情况
- **自定义异常**：使用领域特定的自定义异常类
- **结构化日志**：使用`structlog`或`loguru`进行日志记录
- **数据验证**：使用Pydantic进行数据验证和序列化
- **Result类型**：使用Result类型或Optional建模预期错误
- **特定异常**：使用特定异常类型进行适当的异常处理

### 性能和最佳实践
- **异步操作**：对I/O操作使用async/await
- **连接池**：为数据库操作实现连接池
- **懒加载**：对昂贵操作使用懒加载
- **缓存策略**：实现适当的缓存策略
- **资源管理**：使用上下文管理器进行资源管理

### 关键库和模式
- **pydantic**：数据验证和设置管理
- **sqlalchemy**：支持异步的数据库操作
- **fastapi**：API端点（如需要）
- **pytest**：使用fixtures和参数化进行测试
- **black**：代码格式化
- **mypy**：静态类型检查
- **ruff**或**flake8**：代码检查

## 文档和可解释性

### 文档标准
- **README.md**：新功能、依赖变更或设置步骤修改时更新
- **全面的文档字符串**：遵循Google或NumPy风格
- **复杂逻辑注释**：用内联注释解释推理
- **类型存根**：为外部库维护类型存根（如需要）

### 文档字符串示例
```python
def calculate_optimal_provider(
    symptoms: List[str], 
    insurance_type: str, 
    location: str
) -> OptimalProviderResult:
    """Calculate the optimal medical provider based on user criteria.
    
    Args:
        symptoms: List of user-reported symptoms
        insurance_type: Type of insurance coverage
        location: User's location (state/city)
        
    Returns:
        OptimalProviderResult containing provider details and booking link
        
    Raises:
        NoProvidersFoundError: When no suitable providers are available
        InvalidInsuranceError: When insurance type is not supported
    """
```

## 开发工作流程

### 环境管理
- **虚拟环境**：使用venv、conda或poetry进行依赖隔离
- **版本固定**：在requirements.txt或pyproject.toml中固定依赖版本
- **测试驱动**：实现新功能时先编写测试（TDD方法）
- **预提交钩子**：使用预提交钩子进行代码质量检查
- **CI/CD**：使用Jenkins进行自动化测试和部署

### 架构模式
- **依赖注入**：为服务层组件使用依赖注入
- **仓储模式**：为数据访问实现仓储模式
- **工厂模式**：在适当时为对象创建使用工厂模式
- **SOLID原则**：在类设计中应用SOLID原则
- **关注点分离**：在层之间实现适当的关注点分离（表示层、业务逻辑、数据访问）

## 任务管理

### 任务跟踪
- **检查TASK.md**：开始新任务前检查TASK.md
- **任务添加**：如果任务未列出，添加简要描述和今天的日期
- **完成标记**：完成任务后立即在TASK.md中标记
- **子任务发现**：在开发过程中发现的新子任务或TODO添加到TASK.md的"工作中发现"部分

### 项目意识和上下文
- **始终阅读PLANNING.md**：在新对话开始时了解项目的架构、目标、风格和约束
- **一致的命名约定**：使用PLANNING.md中描述的一致命名约定、文件结构和架构模式
- **模块化设计**：代码组织成清晰分离的模块，按功能或职责分组

## AI行为规则

### 开发约束
- **不要假设缺失的上下文**：不确定时提出问题
- **不要臆造库或函数**：只使用PyPI中已知的、经过验证的Python包
- **确认路径**：在代码或测试中引用之前，始终确认文件路径和模块名称存在
- **不要删除或覆盖现有代码**：除非明确指示或作为TASK.md中任务的一部分
- **使用适当的Python项目结构**：使用虚拟环境和依赖管理

### 文件长度限制
- **1000行限制**：永远不要创建超过1000行代码的文件
- **重构策略**：如果文件接近此限制，通过拆分为模块或辅助文件进行重构
- **模块化组织**：将代码组织成清晰分离的模块，按功能或职责分组

## 集成接口设计

### API集成
- **Mercatus-API集成**：配置API端点和认证信息
- **Mercatus-Client通信**：设置客户端通信协议
- **数据同步**：配置数据库连接和同步机制

### 数据跟踪分析
- **发布链接收集**：从Mercatus-Client接收发布后的作品链接
- **数据聚合**：汇总各平台的发布数据和互动数据
- **效果分析**：提供营销效果的深度分析
- **反馈循环**：基于数据分析优化后续的内容策略

## 部署和运维

### 环境要求
- Python 3.12+
- 消息队列系统（Redis/RabbitMQ）
- VNC服务器
- 浏览器环境
- 相关API密钥配置
- 定时任务调度器（Cron/Celery）

### 部署策略
- **独立部署**：作为重服务需要独立部署
- **用户隔离**：确保用户间的环境完全隔离
- **资源管理**：合理分配计算资源和存储资源
- **监控告警**：实现完善的监控和告警机制

这个PLANNING.md文档将作为项目开发的核心指导文档，确保所有开发活动都遵循统一的架构设计和开发规范。