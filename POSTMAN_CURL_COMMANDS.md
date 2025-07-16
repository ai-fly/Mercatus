# Mercatus API - Postman 导入命令集合

以下是 Mercatus 多智能体内容工厂系统的完整 curl 命令，可直接复制粘贴到 Postman 中导入。

## 📋 导入说明
1. 复制下面的 curl 命令
2. 在 Postman 中点击 "Import" → "Raw text" 
3. 粘贴 curl 命令
4. Postman 会自动解析并创建请求

---

## 1. 健康检查

### 1.1 系统根路径检查
```bash
curl --location 'http://localhost:8000/' \
--header 'Content-Type: application/json'
```

### 1.2 详细健康检查
```bash
curl --location 'http://localhost:8000/health' \
--header 'Content-Type: application/json'
```

---

## 2. 团队管理

### 2.1 创建团队
```bash
curl --location 'http://localhost:8000/api/v1/teams' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "team_name": "Postman测试团队",
    "organization_id": "org-postman-001",
    "owner_username": "postman_admin"
}'
```

### 2.2 获取团队分析数据
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/analytics' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user'
```

---

## 3. 任务管理

### 3.1 创建营销策略规划任务 (Jeff专家)
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "制定Q1社交媒体营销策略",
    "description": "为新产品发布制定全面的社交媒体营销策略，包括平台选择、内容类型规划和时间安排",
    "goal": "提高品牌知名度，增加产品曝光度，提升用户参与度",
    "required_expert_role": "planner",
    "priority": "high",
    "target_platforms": ["twitter", "facebook", "reddit"],
    "target_regions": ["us", "uk", "eu"],
    "content_types": ["text", "text_image", "video"]
}'
```

### 3.2 创建内容生成任务 (Monica专家)
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "生成Twitter产品发布内容",
    "description": "根据营销策略为新产品发布创建Twitter内容，包括推文文案、话题标签和发布时间建议",
    "goal": "创建高质量、有吸引力的Twitter内容以推广新产品",
    "required_expert_role": "executor",
    "priority": "medium",
    "target_platforms": ["twitter"],
    "target_regions": ["us", "uk"],
    "content_types": ["text", "text_image"]
}'
```

### 3.3 创建内容审核任务 (Henry专家)
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "审核社交媒体内容合规性",
    "description": "检查生成的社交媒体内容是否符合各平台政策和地区法规要求",
    "goal": "确保内容合规，降低发布风险",
    "required_expert_role": "evaluator",
    "priority": "high",
    "target_platforms": ["twitter", "facebook", "reddit"],
    "target_regions": ["us", "uk", "eu", "cn"],
    "content_types": ["text", "text_image", "video"]
}'
```

### 3.4 创建低优先级文案任务
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "创建Facebook社区互动内容",
    "description": "为Facebook社区创建日常互动内容，包括问答、投票和用户生成内容引导",
    "goal": "增强社区活跃度和用户参与感",
    "required_expert_role": "executor",
    "priority": "low",
    "target_platforms": ["facebook"],
    "target_regions": ["us"],
    "content_types": ["text"]
}'
```

### 3.5 创建紧急任务
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "紧急危机公关内容制作",
    "description": "针对突发事件快速制作危机公关内容，需要立即审核和发布",
    "goal": "及时应对公关危机，维护品牌形象",
    "required_expert_role": "planner",
    "priority": "urgent",
    "target_platforms": ["twitter", "facebook"],
    "target_regions": ["us", "uk", "eu"],
    "content_types": ["text"]
}'
```

### 3.6 执行指定任务
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks/task_87654321/execute' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data ''
```

---

## 4. 工作流管理

### 4.1 创建完整营销工作流 - 智能手表发布
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/workflows/marketing' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "project_name": "智能手表全球发布营销活动",
    "project_description": "为新款智能手表发布开展全方位社交媒体营销活动，目标是在3个月内提高品牌知名度30%，带来10000+用户参与，实现销售转化5%",
    "target_platforms": ["twitter", "facebook", "reddit", "lemon8"],
    "target_regions": ["us", "uk", "eu", "cn"],
    "content_types": ["text", "text_image", "video"],
    "priority": "urgent"
}'
```

### 4.2 创建中等优先级营销工作流 - 品牌推广
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/workflows/marketing' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "project_name": "品牌形象提升营销活动",
    "project_description": "通过持续的内容营销提升品牌形象，增强用户信任度和忠诚度",
    "target_platforms": ["twitter", "facebook"],
    "target_regions": ["us", "uk"],
    "content_types": ["text", "text_image"],
    "priority": "medium"
}'
```

### 4.3 创建区域化营销工作流 - 中国市场
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/workflows/marketing' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "project_name": "中国市场本土化营销",
    "project_description": "针对中国市场特点，开展本土化社交媒体营销，符合当地文化和法规要求",
    "target_platforms": ["lemon8"],
    "target_regions": ["cn"],
    "content_types": ["text", "text_image", "video"],
    "priority": "high"
}'
```

### 4.4 创建视频营销工作流
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/workflows/marketing' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "project_name": "产品演示视频营销系列",
    "project_description": "创建一系列产品演示和教程视频，在多个平台进行推广",
    "target_platforms": ["twitter", "facebook", "reddit"],
    "target_regions": ["us", "uk", "eu"],
    "content_types": ["video"],
    "priority": "medium"
}'
```

---

## 5. 错误测试用例

### 5.1 无效团队ID测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/invalid-team-123/analytics' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user'
```

### 5.2 无效专家角色测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "无效专家角色测试",
    "description": "测试无效的专家角色",
    "goal": "测试错误处理",
    "required_expert_role": "invalid_expert",
    "priority": "medium"
}'
```

### 5.3 无效平台测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "无效平台测试",
    "description": "测试无效的平台类型",
    "goal": "测试错误处理",
    "required_expert_role": "executor",
    "priority": "medium",
    "target_platforms": ["invalid_platform"]
}'
```

### 5.4 无效优先级测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "无效优先级测试",
    "description": "测试无效的任务优先级",
    "goal": "测试错误处理",
    "required_expert_role": "planner",
    "priority": "super_urgent"
}'
```

### 5.5 执行不存在任务测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks/nonexistent-task-123/execute' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data ''
```

### 5.6 缺少必填字段测试
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "缺少描述字段",
    "goal": "测试缺少必填字段的错误处理",
    "required_expert_role": "executor"
}'
```

---

## 6. 特殊场景测试

### 6.1 多地区多平台任务
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "全球多平台内容推广",
    "description": "在所有支持的平台和地区进行内容推广，测试系统处理复杂场景的能力",
    "goal": "最大化内容覆盖范围和影响力",
    "required_expert_role": "executor",
    "priority": "high",
    "target_platforms": ["twitter", "facebook", "reddit", "lemon8"],
    "target_regions": ["cn", "us", "uk", "eu", "vn", "ae", "ru"],
    "content_types": ["text", "text_image", "video"]
}'
```

### 6.2 最小化参数任务
```bash
curl --location 'http://localhost:8000/api/v1/teams/team_12345678/tasks' \
--header 'Content-Type: application/json' \
--header 'X-User-ID: postman-test-user' \
--data '{
    "title": "最小化参数任务",
    "description": "只使用必填参数的简单任务",
    "goal": "测试最小参数配置",
    "required_expert_role": "planner"
}'
```

---

## 📝 Postman 使用提示

### 🔧 实际使用的 ID 值
**已预设的测试数据：**
- `team_id`: `team_12345678`
- `task_id`: `task_87654321`
- `user_id`: `postman-test-user`

### 📋 测试流程建议
1. **健康检查** → 确认服务正常运行
2. **创建团队** → 使用创建团队命令
3. **创建任务** → 使用不同类型的任务创建命令  
4. **执行任务** → 使用执行任务命令
5. **创建工作流** → 测试完整业务流程
6. **错误测试** → 验证异常处理

### 🎯 状态码说明
- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 📊 响应数据结构
成功响应通常包含：
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

错误响应通常包含：
```json
{
  "error": "Error Type",
  "message": "详细错误信息",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 💡 使用说明
- 所有命令中的 `team_12345678` 和 `task_87654321` 都是示例值
- 在实际使用时，请先执行创建团队命令获取真实的团队ID
- 创建任务后会返回真实的任务ID，用于执行任务
- 每个 curl 命令都可以独立复制到 Postman 中使用

---

*生成时间: 2024年1月 | 适用于 Postman 导入 | 所有变量已替换为具体值* 