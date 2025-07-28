"""
Dependency injection functions for FastAPI
"""
from fastapi import HTTPException, Depends
from app.core.team_manager import TeamManager
from app.services.hybrid_storage import HybridStorageService
from google.auth.transport import requests

# --- Google Auth ---
# Create a global request object for Google Auth.
# This object will cache Google's public keys, which speeds up
# JWT validation significantly.
google_auth_request = requests.Request()


# Global variables (will be set by server.py)
team_manager: TeamManager = None
hybrid_storage_service: HybridStorageService = None


def set_global_services(tm: TeamManager, hss: HybridStorageService):
    """Set global service instances"""
    global team_manager, hybrid_storage_service
    team_manager = tm
    hybrid_storage_service = hss


def get_google_auth_request() -> requests.Request:
    """Returns a cached request object for Google Auth."""
    return google_auth_request


async def get_team_manager() -> TeamManager:
    """Get team manager instance"""
    if team_manager is None:
        raise HTTPException(status_code=503, detail="Team manager not initialized")
    return team_manager


async def get_hybrid_storage_service() -> HybridStorageService:
    """Get hybrid storage service instance"""
    if hybrid_storage_service is None:
        raise HTTPException(status_code=503, detail="Hybrid storage service not initialized")
    return hybrid_storage_service 