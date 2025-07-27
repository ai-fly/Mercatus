"""
Pydantic models for authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional

class GoogleProfile(BaseModel):
    """Represents the user profile information received from Google."""
    email: EmailStr
    name: str
    picture: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class GoogleLoginRequest(BaseModel):
    """Represents the request body for the Google login callback."""
    id_token: str
    profile: GoogleProfile 