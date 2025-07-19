# Mercatus Content Factory

一个基于多智能体协作的内容生成平台，采用 BlackBoard 架构模式，支持多租户团队协作和自动化内容生产。

## 🚀 核心特性

- **🤖 多智能体协作**：Jeff（规划专家）、Monica（执行专家）、Henry（评估专家）
- **📋 BlackBoard 架构**：共享任务状态和协作信息
- **🏢 多租户支持**：支持多个团队独立工作
- **💾 混合存储架构**：PostgreSQL 持久化 + Redis 缓存
- **⚡ 自动化工作流**：智能任务分配和执行
- **📊 实时监控**：团队性能和任务状态监控

## 🏗️ 系统架构

### 混合存储架构

- **PostgreSQL**：主存储，持久化用户、团队、任务、专家数据
- **Redis**：缓存层，存储实时状态、会话数据、临时状态
- **智能同步**：自动保持数据一致性，高性能访问

### 专家系统

- **Jeff（规划专家）**：团队领导者，唯一实例，负责任务规划和策略制定
- **Monica（执行专家）**：内容创建和执行，支持多实例并行（最多3个）
- **Henry（评估专家）**：内容质量评估和审核，支持多实例并行（最多2个）

## 🛠️ 技术栈

- **后端**：Python 3.11+, FastAPI, SQLAlchemy
- **数据库**：PostgreSQL (主存储) + Redis (缓存)
- **消息队列**：RocketMQ
- **AI/LLM**：Anthropic Claude, OpenAI GPT
- **监控**：结构化日志 + 性能指标

## 📦 安装和配置

### 1. 环境要求

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- RocketMQ 4.9+

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd Mercatus

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置

#### 3.1 PostgreSQL 设置

```bash
# 创建数据库
createdb mercatus

# 创建用户（可选）
createuser -P mercatus
```

#### 3.2 Redis 设置

```bash
# 启动 Redis
redis-server

# 或使用 Docker
docker run -d -p 6379:6379 redis:6-alpine
```

### 4. 环境变量配置

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql+asyncpg://mercatus:mercatus@localhost:5432/mercatus
REDIS_URL=redis://localhost:6379/0

# 应用配置
DEBUG=true
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8000

# AI 配置
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# 其他配置
ROCKETMQ_NAMESRV_ADDR=localhost:9876
```

### 5. 数据库初始化

```bash
# 初始化数据库表
python scripts/init_database.py --action init

# 重置数据库（谨慎使用）
python scripts/init_database.py --action reset --confirm
```

### 6. 启动服务

```bash
# 启动应用
python server.py

# 或使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API 使用指南

### 团队管理

#### 创建团队
```bash
curl -X POST "http://localhost:8000/api/v1/teams" \
  -H "Content-Type: application/json" \
  -d '{
    "team_name": "Marketing Team A",
    "organization_id": "org_123",
    "owner_id": "user_456",
    "owner_username": "john_doe"
  }'
```

#### 获取用户团队
```bash
curl "http://localhost:8000/api/v1/users/user_456/teams"
```

### 专家管理

#### 创建专家实例
```bash
curl -X POST "http://localhost:8000/api/v1/teams/team_123/experts" \
  -H "Content-Type: application/json" \
  -d '{
    "expert_role": "executor",
    "instance_name": "Monica - Content Creator",
    "max_concurrent_tasks": 3,
    "specializations": ["social_media", "blog_writing"],
    "is_team_leader": false
  }'
```

#### 获取团队专家
```bash
curl "http://localhost:8000/api/v1/teams/team_123/experts?role=executor"
```

### 任务管理

#### 创建任务
```bash
curl -X POST "http://localhost:8000/api/v1/teams/team_123/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Create Instagram Post",
    "description": "Create engaging Instagram post for new product launch",
    "goal": "Generate high-engagement social media content",
    "required_expert_role": "executor",
    "creator_id": "user_456",
    "priority": "high",
    "target_platforms": ["instagram"],
    "target_regions": ["us", "eu"],
    "content_types": ["image", "caption"]
  }'
```

#### 获取团队任务
```bash
curl "http://localhost:8000/api/v1/teams/team_123/tasks?status=pending"
```

#### 执行任务
```bash
curl -X POST "http://localhost:8000/api/v1/teams/team_123/tasks/task_456/execute"
```

### 规划管理

#### 用户建议重新规划
```bash
curl -X POST "http://localhost:8000/api/v1/teams/team_123/planning/user-suggestion" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_content": "Focus more on video content for better engagement",
    "target_task_ids": ["task_123", "task_456"],
    "user_id": "user_789"
  }'
```

### 性能监控

#### 获取团队性能
```bash
curl "http://localhost:8000/api/v1/teams/team_123/performance"
```

#### 获取 BlackBoard 状态
```bash
curl "http://localhost:8000/api/v1/teams/team_123/blackboard/state"
```

## 🔄 重新规划触发机制

系统支持三种重新规划触发场景：

### 1. 团队启动规划
- **触发时机**：团队创建时自动触发
- **执行者**：Jeff（规划专家）
- **功能**：制定初始工作计划，分配任务给 Monica 和 Henry

### 2. 最大重试失败规划
- **触发时机**：任务达到最大重试次数时
- **执行者**：Jeff（规划专家）
- **功能**：分析失败原因，重新规划任务策略，调整专家配置

### 3. 用户建议规划
- **触发时机**：用户提交改进建议时
- **执行者**：Jeff（规划专家）
- **功能**：分析建议可行性，制定新的规划，创建重新规划任务

## 📊 监控和健康检查

### 健康检查端点
```bash
curl "http://localhost:8000/health"
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

### 日志监控
- 结构化日志输出
- 性能指标记录
- 业务事件追踪
- 错误和异常监控

## 🧪 测试

### 运行测试
```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 性能测试
pytest tests/performance/
```

### 测试覆盖率
```bash
pytest --cov=app tests/
```

## 🚀 部署

### Docker 部署
```bash
# 构建镜像
docker build -t mercatus .

# 运行容器
docker run -d -p 8000:8000 mercatus
```

### 生产环境配置
```bash
# 设置生产环境变量
export DEBUG=false
export LOG_LEVEL=info
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/mercatus_prod
export REDIS_URL=redis://host:6379/0

# 启动服务
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 项目结构

```
Mercatus/
├── app/                    # 应用代码
│   ├── agents/            # 智能体
│   ├── clients/           # 外部客户端
│   ├── config.py          # 配置管理
│   ├── controllers/       # API 控制器
│   ├── core/              # 核心组件
│   ├── database/          # 数据库层
│   ├── experts/           # 专家系统
│   ├── services/          # 业务服务
│   ├── tools/             # 工具集
│   ├── types/             # 类型定义
│   └── utils/             # 工具函数
├── artifacts/             # 生成的文件
├── docs/                  # 文档
├── documents/             # 项目文档
├── logs/                  # 日志文件
├── scripts/               # 脚本文件
├── tests/                 # 测试代码
├── requirements.txt       # 依赖列表
├── server.py             # 服务器入口
└── README.md             # 项目说明
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

- 📧 邮箱：support@mercatus.com
- 📖 文档：[https://docs.mercatus.com](https://docs.mercatus.com)
- 🐛 问题反馈：[GitHub Issues](https://github.com/mercatus/issues)

## 🔮 路线图

### 短期目标
- [ ] 完善混合存储架构
- [ ] 优化专家协作机制
- [ ] 增强监控和告警
- [ ] 改进用户界面

### 中期目标
- [ ] 支持更多内容类型
- [ ] 集成更多 AI 模型
- [ ] 实现智能工作流
- [ ] 添加高级分析功能

### 长期目标
- [ ] 构建内容生成生态
- [ ] 支持多语言和多文化
- [ ] 实现完全自动化
- [ ] 扩展到其他行业

## 用户认证与Google邮箱登录

系统支持Google邮箱OAuth授权登录：
- 账号以邮箱为唯一标识
- 若邮箱不存在则自动注册
- 登录成功后返回JWT令牌

### 环境变量配置
- `GOOGLE_CLIENT_ID`：Google OAuth客户端ID
- `JWT_SECRET`：用于签发JWT的密钥

### API
- `POST /api/v1/auth/google-login`
  - 请求体: `{ "token": "<Google OAuth id_token>" }`
  - 返回: `{ "access_token": "...", "token_type": "bearer", "user_email": "..." }`