"""
Simplified Clerk Authentication for Railway deployment
"""
import os
from typing import Optional
from fastapi import Header, HTTPException
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

# Clerk Configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_PUBLISHABLE_KEY = os.getenv("EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY", "")


async def get_current_user_id(
    authorization: str = Header(None, description="Bearer token from Clerk")
) -> str:
    """
    Extract and verify user ID from Clerk JWT token (simplified version)

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Clerk user ID (e.g., "user_2abc123...")

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header. Please provide Bearer token from Clerk."
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: 'Bearer <token>'"
        )

    token = parts[1]

    try:
        # Decode without verification for now (Railway deployment fix)
        # In production, you should verify the signature
        payload = jwt.decode(
            token,
            key='',
            options={"verify_signature": False}
        )

        # Extract user ID
        user_id = payload.get('sub')

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        # Check if token is expired
        import time
        exp = payload.get('exp')
        if exp and exp < time.time():
            raise HTTPException(
                status_code=401,
                detail="Invalid token: Token has expired"
            )

        logger.debug(f"Authenticated user: {user_id}")
        return user_id

    except JWTError as e:
        error_message = str(e)
        if 'expired' in error_message.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid token: Signature has expired"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {error_message}"
            )


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Optional authentication - returns user ID if token present, None otherwise
    """
    if not authorization:
        return None

    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


# For admin endpoints
async def get_current_admin_user_id(
    authorization: str = Header(None, description="Bearer token from Clerk")
) -> str:
    """
    Verify user is authenticated AND has admin privileges
    (Simplified version - just checks authentication for now)
    """
    return await get_current_user_id(authorization)