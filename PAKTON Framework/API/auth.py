"""
Description: 
    Authentication and authorization utilities for validating Supabase JWT tokens.
    Provides FastAPI dependencies for protecting endpoints with user authentication.
    
Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from fastapi import HTTPException, Header, status
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from .config import Config
from .logger import logger


class SupabaseUser:
    """
    Represents an authenticated Supabase user extracted from JWT token.
    """
    def __init__(self, payload: Dict[str, Any]):
        self.user_id: str = payload.get("sub", "")
        self.email: Optional[str] = payload.get("email")
        self.role: str = payload.get("role", "")
        self.aud: str = payload.get("aud", "")
        self.exp: int = payload.get("exp", 0)
        self.iat: int = payload.get("iat", 0)
        self.phone: Optional[str] = payload.get("phone")
        self.app_metadata: Dict[str, Any] = payload.get("app_metadata", {})
        self.user_metadata: Dict[str, Any] = payload.get("user_metadata", {})
        self.raw_payload: Dict[str, Any] = payload
    
    def __repr__(self):
        return f"SupabaseUser(user_id={self.user_id}, email={self.email}, role={self.role})"
    
    def to_dict(self):
        """Convert user to dictionary for logging/debugging."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
        }


async def verify_jwt_token(authorization: str = Header(None)) -> SupabaseUser:
    """
    Verify and decode a Supabase JWT token from the Authorization header.
    
    This function:
    1. Extracts the Bearer token from the Authorization header
    2. Verifies the token signature using the Supabase JWT secret
    3. Validates token claims (expiration, audience, etc.)
    4. Returns a SupabaseUser object with user information
    
    Args:
        authorization: The Authorization header (format: "Bearer <token>")
        
    Returns:
        SupabaseUser object containing user information from the token
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
        
    Example:
        @app.get("/protected")
        async def protected_endpoint(user: SupabaseUser = Depends(verify_jwt_token)):
            return {"message": f"Hello {user.email}"}
    """
    # Check if Authorization header is present
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract Bearer token
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ", 1)[1]
    
    try:
        # Verify and decode the token using the JWT secret
        payload = jwt.decode(
            token,
            Config.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],  # Supabase uses HS256 symmetric key
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,  # Supabase tokens may have different audience values
            }
        )
        
        # Create and return SupabaseUser object
        user = SupabaseUser(payload)
        
        logger.info(f"Successfully authenticated user: {user.user_id} ({user.email})")
        
        return user
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.JWTClaimsError as e:
        logger.warning(f"JWT claims validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}",
        )
    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication",
        )


async def get_optional_user(authorization: str = Header(None)) -> Optional[SupabaseUser]:
    """
    Optional authentication dependency that returns None if no valid token is provided.
    Useful for endpoints that have optional authentication.
    
    Args:
        authorization: The Authorization header (format: "Bearer <token>")
        
    Returns:
        SupabaseUser object if valid token is provided, None otherwise
        
    Example:
        @app.get("/public-or-private")
        async def endpoint(user: Optional[SupabaseUser] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            else:
                return {"message": "Hello anonymous user"}
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        return await verify_jwt_token(authorization)
    except HTTPException:
        return None


async def get_current_user(authorization: str = Header(None)) -> Optional[SupabaseUser]:
    """
    Conditional authentication dependency based on ENABLE_AUTHENTICATION config.
    
    - If ENABLE_AUTHENTICATION=true: Requires valid JWT token (raises 401 if missing/invalid)
    - If ENABLE_AUTHENTICATION=false: Returns None (authentication disabled for development)
    
    This allows you to easily toggle authentication on/off via environment variable.
    Use this dependency instead of verify_jwt_token directly for conditional auth.
    
    Args:
        authorization: The Authorization header (format: "Bearer <token>")
        
    Returns:
        SupabaseUser object if authentication is enabled and token is valid,
        None if authentication is disabled
        
    Raises:
        HTTPException: If authentication is enabled but token is missing/invalid
        
    Example:
        @app.post("/protected")
        async def protected_endpoint(user: Optional[SupabaseUser] = Depends(get_current_user)):
            # If auth is enabled, user will be a SupabaseUser object
            # If auth is disabled, user will be None
            if user:
                return {"message": f"Hello {user.email}"}
            else:
                return {"message": "Authentication disabled (development mode)"}
    """
    if not Config.ENABLE_AUTHENTICATION:
        logger.info("Authentication disabled - allowing request without token")
        return None
    
    return await verify_jwt_token(authorization)
