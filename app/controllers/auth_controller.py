import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from app.services.hybrid_storage import HybridStorageService
from app.dependencies import get_hybrid_storage_service
from app.types.output import AuthTokenResponse
from jose import jwt
from authlib.integrations.starlette_client import OAuth
import os
from datetime import datetime, timedelta

# 路由器
router = APIRouter()
logger = logging.getLogger("AuthController")

# Google 配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET", "c95cbe5766b2e01994e4ed75b9cadcbb7201d30cf3fd7bf9113addbf3da88379")
JWT_ALGORITHM = "RS256"  # 与JWT中间件保持一致
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 配置OAuth
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/auth/google/login")
async def login_via_google(request: Request):
    """
    Redirects to Google's authentication page.
    """
    redirect_uri = request.url_for('auth_via_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback", response_model=AuthTokenResponse)
async def auth_via_google(
    request: Request,
    hybrid_storage: HybridStorageService = Depends(get_hybrid_storage_service)
):
    """
    Handles the callback from Google, creates/logs in the user, and returns a JWT token.
    """
    try:
        token_data = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Could not authorize access token: {e}")
        raise HTTPException(status_code=401, detail="Could not authorize access token")

    user_info = await oauth.google.parse_id_token(request, token_data)
    email = user_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="No email found in Google token")

    user_result = await hybrid_storage.get_or_create_user_by_email(email=email)
    if user_result.get("status") != "success":
        logger.error(f"User creation/retrieval failed: {user_result}")
        raise HTTPException(status_code=500, detail="User creation or retrieval failed")

    user = user_result["user"]
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "email": email,
        "user_id": user["user_id"],
        "exp": expire
    }
    
    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return AuthTokenResponse(access_token=access_token, user_email=email) 