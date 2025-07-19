
## 用户登录流程（Google OAuth）

1. 前端集成Google OAuth登录按钮，获取id_token
2. 前端将id_token通过POST发送到`/api/v1/auth/google-login`
3. 后端验证Google token，若邮箱不存在则自动注册
4. 后端返回JWT令牌，前端保存并用于后续API请求

接口：
- `POST /api/v1/auth/google-login`，参数：`{ "token": "<Google id_token>" }`
- 返回：`{ "access_token": "...", "token_type": "bearer", "user_email": "..." }`


