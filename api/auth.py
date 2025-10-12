"""
Authentication Middleware and Utilities

Handles Clerk JWT verification and user authentication
"""
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
from typing import Optional
import os
from functools import lru_cache

# Clerk Configuration
CLERK_PUBLISHABLE_KEY = os.getenv("EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "")  # e.g., https://your-app.clerk.accounts.dev

# JWT Configuration
ALGORITHM = "RS256"


@lru_cache()
def get_clerk_public_key():
    """
    Get Clerk's public key for JWT verification

    Note: In production, you should fetch this from Clerk's JWKS endpoint
    For now, we'll use a simplified approach
    """
    # TODO: Implement JWKS fetching
    # For now, return None and we'll verify using Clerk API
    return None


async def get_current_user_id(
    authorization: str = Header(None, description="Bearer token from Clerk")
) -> str:
    """
    Extract and verify user ID from Clerk JWT token

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
        # Decode without verification first to get the payload
        # In production, you should verify the signature using Clerk's public key
        payload = jwt.decode(
            token,
            key='',  # Empty key when not verifying
            options={"verify_signature": False}  # TODO: Enable signature verification
        )

        # Extract user ID from token
        user_id = payload.get("sub")  # Clerk uses 'sub' for user ID

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        return user_id

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Optional authentication - returns user ID if token present, None otherwise

    Useful for endpoints that work both with and without authentication
    """
    if not authorization:
        return None

    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None


def verify_admin_role(user_id: str) -> bool:
    """
    Check if user has admin role

    TODO: Implement proper role checking from database or Clerk
    For now, we'll use environment variable
    """
    admin_users = os.getenv("ADMIN_USER_IDS", "").split(",")
    return user_id in admin_users
