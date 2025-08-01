import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import EmailStr
from app.services.hybrid_storage import HybridStorageService
from app.dependencies import get_hybrid_storage_service, get_google_auth_request
from app.types.output import AuthTokenResponse
from app.types.auth import GoogleLoginRequest
from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from datetime import datetime, timedelta, timezone
import time
_request = requests.Request()
# 路由器
router = APIRouter()
logger = logging.getLogger("AuthController")

# Google 配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET", "c95cbe5766b2e01994e4ed75b9cadcbb7201d30cf3fd7bf9113addbf3da88379")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/auth/google/login", response_model=AuthTokenResponse)
async def auth_via_google(
    login_data: GoogleLoginRequest,
    hybrid_storage: HybridStorageService = Depends(get_hybrid_storage_service),
):
    """
    Validates a Google ID token, creates/logs in the user with full profile details,
    and returns a JWT token.
    """
    logger.debug("login_data: %s", login_data)
    try:
        # TIMING: Start token validation
        start_time = time.time()
        logger.info("Starting Google ID token validation...")

        # Validate the ID token using the google-auth library
        idinfo = id_token.verify_oauth2_token(
            login_data.id_token, _request, GOOGLE_CLIENT_ID
        )

        validation_time = time.time() - start_time
        logger.info(f"Token validation finished in {validation_time:.4f} seconds.")

        # Security check: ensure the email in the validated token matches the one in the profile.
        if idinfo.get("email") != login_data.profile.email:
            raise HTTPException(
                status_code=400, detail="Token email does not match profile email"
            )

    except ValueError as e:
        logger.error(f"Could not validate ID token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate ID token. It may be expired or invalid.",
        )

    # Now that the token is validated, you can safely use the profile data.
    profile = login_data.profile

    # You should adapt your user creation logic to accept the new details.
    # For example, create a dictionary with the full user data.
    user_details_to_save = {
        "email": profile.email,
        "full_name": profile.name,
        "picture_url": profile.picture,
        "given_name": profile.given_name,
        "family_name": profile.family_name,
    }

    # TIMING: Start database operation
    start_time_db = time.time()
    logger.info("Starting user get/create database operation...")

    # Pass the full user details to your database service.
    # (You may need to update get_or_create_user_by_email to handle these new fields)
    user_result = await hybrid_storage.get_or_create_user_by_email(user_details_to_save)

    db_time = time.time() - start_time_db
    logger.info(f"Database operation finished in {db_time:.4f} seconds.")

    if user_result.get("status") != "success":
        logger.error(f"User creation/retrieval failed: {user_result}")
        raise HTTPException(status_code=500, detail="User creation or retrieval failed")

    user = user_result["user"]

    # Create the JWT payload. You can add more user info here if needed.
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": profile.email,
        "email": profile.email,
        "user_id": user["user_id"],
        "name": profile.name,
        "picture": profile.picture,
        "exp": expire,
    }

    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return AuthTokenResponse(access_token=access_token, user_email=profile.email)
