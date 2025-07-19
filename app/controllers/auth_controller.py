import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import EmailStr
from app.services.hybrid_storage import HybridStorageService
from app.dependencies import get_hybrid_storage_service
from app.types.output import GoogleOAuthLoginRequest, AuthTokenResponse
from jose import jwt
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx
import os

# 路由器
router = APIRouter()
logger = logging.getLogger("AuthController")

# Google 配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-change-in-production")
GOOGLE_JWT_ALGORITHM = "HS256"  # 可根据实际情况调整
GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

async def verify_google_token(token: str) -> EmailStr:
    """验证Google OAuth token并返回邮箱"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": token})
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        data = resp.json()
        email = data.get("email")
        aud = data.get("aud")
        if not email or (GOOGLE_CLIENT_ID and aud != GOOGLE_CLIENT_ID):
            raise HTTPException(status_code=401, detail="Invalid Google token or client id")
        return email

@router.post("/auth/google-login", response_model=AuthTokenResponse)
async def google_login(
    req: GoogleOAuthLoginRequest,
    hybrid_storage: HybridStorageService = Depends(get_hybrid_storage_service)
):
    """Google邮箱OAuth登录，自动注册新用户，返回JWT令牌"""
    email = await verify_google_token(req.token)
    user_result = await hybrid_storage.get_or_create_user_by_email(email=email)
    if user_result["status"] != "success":
        logger.error(f"User creation failed: {user_result}")
        raise HTTPException(status_code=500, detail="User creation failed")
    # 生成JWT
    payload = {
        "sub": email,
        "email": email,
        "user_id": user_result["user"]["user_id"],
    }
    token = jwt.encode(payload, GOOGLE_JWT_SECRET, algorithm=GOOGLE_JWT_ALGORITHM)
    return AuthTokenResponse(access_token=token, user_email=email) 