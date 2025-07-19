# Mercatus Content Factory - 系统规划文档

## 1. 项目概述

Mercatus Content Factory 是一个基于多智能体协作的内容生成平台，采用 BlackBoard 架构模式，支持多租户团队协作和自动化内容生产。

### 1.1 核心特性

- **Google邮箱OAuth登录**：支持Google邮箱授权登录，邮箱为唯一账号标识，自动注册新用户
- **多智能体协作**：Jeff（规划专家）、Monica（执行专家）、Henry（评估专家）
- **BlackBoard 架构**：共享任务状态和协作信息
- **多租户支持**：支持多个团队独立工作
- **混合存储架构**：PostgreSQL 持久化 + Redis 缓存
- **自动化工作流**：智能任务分配和执行
- **实时监控**：团队性能和任务状态监控

### 1.2 技术栈

- **后端**：Python 3.11+, FastAPI, SQLAlchemy
- **数据库**：PostgreSQL (主存储) + Redis (缓存)
- **消息队列**：RocketMQ
- **AI/LLM**：Anthropic Claude, OpenAI GPT
- **监控**：结构化日志 + 性能指标

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Mobile App    │    │   API Clients   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     FastAPI Gateway       │
                    │      (Load Balancer)      │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Mercatus Backend       │
                    │                           │
                    │  ┌─────────────────────┐  │
                    │  │   Team Manager      │  │
                    │  │   (Multi-tenant)    │  │
                    │  └─────────┬───────────┘  │
                    │            │              │
                    │  ┌─────────▼───────────┐  │
                    │  │   BlackBoard        │  │
                    │  │   (Task Queue)      │  │
                    │  └─────────┬───────────┘  │
                    │            │              │
                    │  ┌─────────▼───────────┐  │
                    │  │   Expert System     │  │
                    │  │   (Jeff/Monica/Henry)│  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   PostgreSQL      │  │      Redis        │  │     RocketMQ      │
│   (主存储)         │  │   (缓存/实时状态)   │  │   (消息队列)       │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### 2.2 混合存储架构

#### 2.2.1 存储策略

**PostgreSQL (主存储)**
- 用户数据、团队信息
- 任务数据、专家实例信息
- 任务分配、事件记录
- 团队配置、性能指标

**Redis (缓存层)**
- 实时任务状态
- 专家实例状态
- 团队状态缓存
- 会话数据、临时状态

#### 2.2.2 数据同步机制

```python
# 混合存储服务示例
class HybridStorageService:
    async def create_task(self, task_data):
        # 1. 写入 PostgreSQL
        task = await self.task_repo.create(task_data)
        
        # 2. 更新 Redis 缓存
        await self.redis_cache.set(f"task:{task.id}", task.to_dict())
        
        # 3. 更新状态索引
        await self.update_task_status_index(task.id, "pending")
        
        return {"status": "success", "task": task.to_dict()}
```

### 2.3 核心组件

#### 2.3.1 Team Manager (团队管理器)

**职责**：
- 多租户团队管理
- 专家实例生命周期管理
- 团队配置和权限控制
- 性能监控和指标收集

**关键特性**：
- 支持一个用户创建多个团队
- 团队间数据隔离
- 专家实例自动扩缩容
- 团队性能分析和优化

#### 2.3.2 BlackBoard (任务黑板)

**职责**：
- 任务状态管理和分发
- 专家实例任务分配
- 任务依赖关系处理
- 实时状态同步

**关键特性**：
- 混合存储支持（PostgreSQL + Redis）
- 任务优先级管理
- 失败重试机制
- 实时状态更新

#### 2.3.3 Expert System (专家系统)

**Jeff (规划专家)**
- 团队领导者，唯一实例
- 负责任务规划和策略制定
- 监控团队整体进度
- 处理用户建议和重新规划

**Monica (执行专家)**
- 内容创建和执行
- 支持多实例并行工作
- 自动扩缩容（最多3个实例）
- 专注于内容生成任务

**Henry (评估专家)**
- 内容质量评估和审核
- 支持多实例并行工作
- 自动扩缩容（最多2个实例）
- 确保内容质量和合规性

## 3. 数据模型

### 3.1 核心实体

#### 3.1.1 User (用户)
```python
class User(Base):
    user_id: str          # 用户唯一标识
    username: str         # 用户名
    email: str           # 邮箱（唯一，OAuth登录主键）
    organization_id: str # 组织ID
    is_active: bool      # 是否激活
    created_at: datetime # 创建时间
    updated_at: datetime # 更新时间
```
> 说明：邮箱为唯一账号标识，支持Google OAuth登录，若邮箱不存在则自动注册。

#### 3.1.2 Team (团队)
```python
class Team(Base):
    team_id: str                    # 团队唯一标识
    team_name: str                  # 团队名称
    organization_id: str           # 组织ID
    owner_id: str                  # 所有者ID
    is_active: bool                # 是否激活
    max_jeff_instances: int        # Jeff实例限制 (固定为1)
    max_monica_instances: int      # Monica实例限制 (最多3个)
    max_henry_instances: int       # Henry实例限制 (最多2个)
    auto_scaling_enabled: bool     # 自动扩缩容
    task_queue_limit: int          # 任务队列限制
    concurrent_task_limit: int     # 并发任务限制
    total_tasks_completed: int     # 完成任务总数
    team_performance_score: float  # 团队绩效分数
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间
```

#### 3.1.3 BlackboardTask (任务)
```python
class BlackboardTask(Base):
    task_id: str                   # 任务唯一标识
    team_id: str                   # 所属团队ID
    title: str                     # 任务标题
    description: str               # 任务描述
    goal: str                      # 任务目标
    required_expert_role: str      # 所需专家角色
    priority: str                  # 优先级
    status: str                    # 任务状态
    target_platforms: List[str]    # 目标平台
    target_regions: List[str]      # 目标地区
    content_types: List[str]       # 内容类型
    due_date: datetime             # 截止日期
    dependencies: List[dict]       # 依赖关系
    parent_task_id: str            # 父任务ID
    creator_id: str                # 创建者ID
    retry_count: int               # 重试次数
    max_retries: int               # 最大重试次数
    failure_reason: str            # 失败原因
    metadata: dict                 # 元数据
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间
```

#### 3.1.4 ExpertInstance (专家实例)
```python
class ExpertInstance(Base):
    instance_id: str               # 实例唯一标识
    team_id: str                   # 所属团队ID
    expert_role: str               # 专家角色
    instance_name: str             # 实例名称
    status: str                    # 实例状态
    max_concurrent_tasks: int      # 最大并发任务数
    current_task_count: int        # 当前任务数
    specializations: List[str]     # 专业领域
    performance_metrics: dict      # 性能指标
    is_team_leader: bool           # 是否为团队领导
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间
```

### 3.2 关系模型

```
User (1) ──── (N) Team
Team (1) ──── (N) TeamMember
Team (1) ──── (N) BlackboardTask
Team (1) ──── (N) ExpertInstance
BlackboardTask (1) ──── (1) TaskAssignment
ExpertInstance (1) ──── (N) TaskAssignment
BlackboardTask (1) ──── (N) TaskEvent
```

## 4. API 设计

### 4.0 用户认证 API
- `POST /api/v1/auth/google-login`：Google邮箱OAuth登录，自动注册新用户，返回JWT令牌

### 4.1 团队管理 API

#### 4.1.1 创建团队
```http
POST /api/v1/teams
Content-Type: application/json

{
    "team_name": "Marketing Team A",
    "organization_id": "org_123",
    "owner_id": "user_456",
    "owner_username": "john_doe"
}
```

#### 4.1.2 获取用户团队
```http
GET /api/v1/users/{user_id}/teams
```

#### 4.1.3 获取团队信息
```http
GET /api/v1/teams/{team_id}
```

### 4.2 专家管理 API

> 默认专家实例（Jeff、Monica、Henry）会在团队创建时自动初始化，无需单独调用接口。
> 团队扩容/添加额外专家实例的接口已移除，所有专家实例均在团队创建时自动生成。

#### 4.2.2 获取团队专家
```http
GET /api/v1/teams/{team_id}/experts?role=executor
```

### 4.3 任务管理 API

#### 4.3.1 创建任务
```http
POST /api/v1/teams/{team_id}/tasks
Content-Type: application/json

{
    "title": "Create Instagram Post",
    "description": "Create engaging Instagram post for new product launch",
    "goal": "Generate high-engagement social media content",
    "required_expert_role": "executor",
    "creator_id": "user_456",
    "priority": "high",
    "target_platforms": ["instagram"],
    "target_regions": ["us", "eu"],
    "content_types": ["image", "caption"]
}
```

#### 4.3.2 获取团队任务
```http
GET /api/v1/teams/{team_id}/tasks?status=pending
```

#### 4.3.3 执行任务
```http
POST /api/v1/teams/{team_id}/tasks/{task_id}/execute
```

### 4.4 规划管理 API

#### 4.4.1 用户建议重新规划
```http
POST /api/v1/teams/{team_id}/planning/user-suggestion
Content-Type: application/json

{
    "suggestion_content": "Focus more on video content for better engagement",
    "target_task_ids": ["task_123", "task_456"],
    "user_id": "user_789"
}
```

### 4.5 性能监控 API

#### 4.5.1 获取团队性能
```http
GET /api/v1/teams/{team_id}/performance
```

#### 4.5.2 获取 BlackBoard 状态
```http
GET /api/v1/teams/{team_id}/blackboard/state
```

## 5. 工作流程

### 5.1 团队创建流程

1. **用户创建团队**
   - 验证用户权限
   - 创建团队记录（PostgreSQL）
   - 初始化 BlackBoard 实例
   - 创建默认专家实例（Jeff、Monica、Henry）【自动完成】
   - 启动监控服务

2. **专家实例初始化**
   - Jeff：创建唯一团队领导实例
   - Monica：创建默认执行实例
   - Henry：创建默认评估实例
   - 注册到 BlackBoard

### 5.2 任务执行流程

1. **任务创建**
   - 用户提交任务请求
   - 验证任务参数和权限
   - 创建任务记录（PostgreSQL）
   - 更新 Redis 状态缓存
   - 发送任务创建事件

2. **任务分配**
   - BlackBoard 根据专家角色筛选可用实例
   - 考虑负载均衡和优先级
   - 分配任务给合适的专家实例
   - 更新任务状态为 "assigned"

3. **任务执行**
   - 专家实例接收任务
   - 更新任务状态为 "in_progress"
   - 执行任务逻辑
   - 生成结果和输出

4. **任务完成**
   - 更新任务状态为 "completed"
   - 存储执行结果
   - 更新性能指标
   - 触发后续任务（如果有依赖）

### 5.3 重新规划触发机制

#### 5.3.1 团队启动规划
- 团队创建时自动触发
- Jeff 制定初始工作计划
- 分配任务给 Monica 和 Henry

#### 5.3.2 最大重试失败规划
- 任务达到最大重试次数时触发
- 分析失败原因和模式
- Jeff 重新规划任务策略
- 调整专家配置或任务参数

#### 5.3.3 用户建议规划
- 用户提交改进建议时触发
- 分析建议的可行性和影响
- Jeff 评估并制定新的规划
- 创建重新规划任务

## 6. 部署和运维

### 6.1 环境配置

#### 6.1.1 开发环境
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://mercatus:mercatus@localhost:5432/mercatus_dev
REDIS_URL=redis://localhost:6379/0

# 应用配置
DEBUG=true
LOG_LEVEL=debug
HOST=0.0.0.0
PORT=8000
```

#### 6.1.2 生产环境
```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://mercatus:${DB_PASSWORD}@${DB_HOST}:5432/mercatus_prod
REDIS_URL=redis://${REDIS_HOST}:6379/0

# 应用配置
DEBUG=false
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8000
```

### 6.2 数据库初始化

```bash
# 初始化数据库
python scripts/init_database.py --action init

# 重置数据库（谨慎使用）
python scripts/init_database.py --action reset --confirm
```

### 6.3 服务启动

```bash
# 启动应用
python server.py

# 或使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 6.4 监控和日志

#### 6.4.1 日志配置
- 结构化日志输出
- 性能指标记录
- 业务事件追踪
- 错误和异常监控

#### 6.4.2 健康检查
```http
GET /health
```

响应示例：
```json
{
    "status": "healthy",
    "service": "Mercatus Content Factory",
    "version": "1.0.0",
    "database": "connected",
    "redis": "connected"
}
```

## 7. 安全考虑

### 7.1 数据安全
- 数据库连接加密
- Redis 访问控制
- 敏感数据加密存储
- 定期数据备份

### 7.2 API 安全
- 请求速率限制
- 输入验证和清理
- CORS 配置
- 错误信息脱敏

### 7.3 访问控制
- 用户认证和授权
- 团队数据隔离
- 角色权限管理
- API 访问审计

## 8. 性能优化

### 8.1 数据库优化
- 连接池管理
- 索引优化
- 查询优化
- 读写分离

### 8.2 缓存策略
- Redis 缓存热点数据
- 缓存失效策略
- 缓存预热机制
- 缓存监控

### 8.3 并发处理
- 异步任务处理
- 专家实例负载均衡
- 任务队列优化
- 资源限制管理

## 9. 扩展性设计

### 9.1 水平扩展
- 无状态 API 服务
- 数据库读写分离
- Redis 集群支持
- 负载均衡

### 9.2 功能扩展
- 插件化专家系统
- 可配置工作流
- 自定义任务类型
- 第三方集成

### 9.3 多租户扩展
- 组织级别隔离
- 资源配额管理
- 计费和限制
- 多区域部署

## 10. 测试策略

### 10.1 单元测试
- 核心业务逻辑测试
- 数据模型测试
- API 端点测试
- 专家系统测试

### 10.2 集成测试
- 数据库集成测试
- Redis 缓存测试
- 专家协作测试
- 端到端工作流测试

### 10.3 性能测试
- 负载测试
- 压力测试
- 并发测试
- 数据库性能测试

## 11. 未来规划

### 11.1 短期目标
- 完善混合存储架构
- 优化专家协作机制
- 增强监控和告警
- 改进用户界面

### 11.2 中期目标
- 支持更多内容类型
- 集成更多 AI 模型
- 实现智能工作流
- 添加高级分析功能

### 11.3 长期目标
- 构建内容生成生态
- 支持多语言和多文化
- 实现完全自动化
- 扩展到其他行业