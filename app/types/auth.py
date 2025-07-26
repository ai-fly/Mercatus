"""
Pydantic models for authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr

class GoogleProfile(BaseModel):
    """Represents the user profile information received from Google."""
    email: EmailStr
    name: str
    picture: str
    given_name: str
    family_name: str

class GoogleLoginRequest(BaseModel):
    """Represents the request body for the Google login callback."""
    id_token: str
    profile: GoogleProfile 