import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from jose import jwt, JWTError
import os

logger = logging.getLogger(__name__)

# 从环境变量或配置中获取JWT密钥和算法
JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "c95cbe5766b2e01994e4ed75b9cadcbb7201d30cf3fd7bf9113addbf3da88379",
)
JWT_ALGORITHM = "HS256"

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # 定义不需要JWT验证的路径
        excluded_paths = [
            "/docs",
            "/openapi.json",
            "/health",
            "/",
            "/api/v1/auth/google/login",
        ]
        
        # 检查当前请求路径是否在排除列表中
        if request.url.path in excluded_paths:
            return await call_next(request)
        
        # 从请求头中获取JWT
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Missing Authorization header")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"}
            )
        
        # 验证JWT格式
        parts = auth_header.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            logger.warning(f"Invalid Authorization header format: {auth_header}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format"}
            )
            
        token = parts[1]
        
        try:
            # 解码并验证JWT
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # 将用户信息附加到请求状态中，以便后续使用
            request.state.user = payload
            
        except JWTError as e:
            logger.error(f"JWT validation failed: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred during token validation: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

        response = await call_next(request)
        return response 
