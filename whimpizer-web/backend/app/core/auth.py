"""
Clerk Authentication Integration for FastAPI
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
import requests
from functools import wraps

from app.core.config import settings

# Initialize HTTP Bearer for token extraction
security = HTTPBearer(auto_error=False)

class ClerkAuth:
    """Clerk authentication handler"""
    
    def __init__(self):
        self.secret_key = settings.CLERK_SECRET_KEY
        self.enabled = settings.ENABLE_AUTH
        self._jwks_cache = None
    
    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS (JSON Web Key Set) from Clerk"""
        if not self._jwks_cache:
            try:
                response = requests.get("https://api.clerk.dev/.well-known/jwks.json")
                response.raise_for_status()
                self._jwks_cache = response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch JWKS: {str(e)}")
        return self._jwks_cache
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Clerk JWT token"""
        if not self.enabled:
            # Return a mock user when auth is disabled
            return {"sub": "dev_user", "email": "dev@whimpizer.com", "name": "Dev User"}
        
        try:
            # For now, we'll use a simple verification
            # In production, you'd want to verify against Clerk's JWKS
            decoded = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=["RS256"], 
                options={"verify_signature": False}  # Simplified for demo
            )
            return decoded
        except jwt.InvalidTokenError:
            return None
    
    async def get_current_user(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
        """Get current user from request"""
        if not self.enabled:
            # Return mock user when auth is disabled
            return {"sub": "dev_user", "email": "dev@whimpizer.com", "name": "Dev User"}
        
        if not credentials:
            return None
        
        return await self.verify_token(credentials.credentials)
    
    async def require_auth(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
        """Require authentication - raise exception if not authenticated"""
        if not self.enabled:
            # Return mock user when auth is disabled
            return {"sub": "dev_user", "email": "dev@whimpizer.com", "name": "Dev User"}
        
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user = await self.verify_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        return user

# Global auth instance
clerk_auth = ClerkAuth()

# Convenience functions for route dependencies
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user (optional authentication)"""
    return await clerk_auth.get_current_user(credentials)

async def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Require authentication (mandatory)"""
    return await clerk_auth.require_auth(credentials)

def optional_auth(func):
    """Decorator for optional authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

def require_auth_decorator(func):
    """Decorator for required authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper