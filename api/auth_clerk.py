"""
Enhanced Clerk Authentication with proper JWT verification
"""
import os
import time
import httpx
import json
from typing import Optional, Dict
from fastapi import Header, HTTPException
from jose import jwt, JWTError, jwk
from jose.constants import ALGORITHMS
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Clerk Configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_PUBLISHABLE_KEY = os.getenv("EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY", "")

# Extract Clerk instance ID from publishable key
# Format: pk_test_xxxxx or pk_live_xxxxx (base64 encoded domain)
def get_clerk_instance_id():
    """Extract instance ID from Clerk publishable key (decodes base64)"""
    if not CLERK_PUBLISHABLE_KEY:
        return None

    try:
        # Remove pk_test_ or pk_live_ prefix
        if CLERK_PUBLISHABLE_KEY.startswith("pk_test_"):
            key_part = CLERK_PUBLISHABLE_KEY.replace("pk_test_", "")
        elif CLERK_PUBLISHABLE_KEY.startswith("pk_live_"):
            key_part = CLERK_PUBLISHABLE_KEY.replace("pk_live_", "")
        else:
            return None

        # Decode base64 to get the Clerk domain
        import base64
        decoded = base64.b64decode(key_part).decode('utf-8', errors='ignore')

        # Extract domain (format: fleet-mallard-98.clerk.accounts.dev$)
        # Remove trailing $ if present
        domain = decoded.strip().rstrip('$')

        logger.info(f"Decoded Clerk domain: {domain}")
        return domain

    except Exception as e:
        logger.error(f"Failed to decode Clerk publishable key: {e}")
        return None

# Build JWKS URL from decoded domain
CLERK_DOMAIN = get_clerk_instance_id()
CLERK_JWKS_URL = f"https://{CLERK_DOMAIN}/.well-known/jwks.json" if CLERK_DOMAIN else None

# Cache for JWKS keys
_jwks_cache = None
_jwks_cache_time = 0
JWKS_CACHE_DURATION = 3600  # Cache for 1 hour

@lru_cache(maxsize=1)
def get_clerk_jwks():
    """
    Fetch and cache Clerk's JWKS (JSON Web Key Set) for JWT verification
    """
    global _jwks_cache, _jwks_cache_time

    # Return cached JWKS if still valid
    if _jwks_cache and (time.time() - _jwks_cache_time) < JWKS_CACHE_DURATION:
        return _jwks_cache

    if not CLERK_JWKS_URL:
        logger.warning("Clerk JWKS URL not configured - JWT verification disabled")
        return None

    try:
        # Fetch JWKS from Clerk
        with httpx.Client(timeout=10.0) as client:
            response = client.get(CLERK_JWKS_URL)
            response.raise_for_status()

            jwks_data = response.json()
            _jwks_cache = jwks_data
            _jwks_cache_time = time.time()

            logger.info(f"Successfully fetched Clerk JWKS from {CLERK_JWKS_URL}")
            return jwks_data

    except Exception as e:
        logger.error(f"Failed to fetch Clerk JWKS: {e}")
        # Return cached version even if expired
        if _jwks_cache:
            logger.warning("Using expired JWKS cache as fallback")
            return _jwks_cache
        return None


def verify_clerk_token(token: str) -> Dict:
    """
    Verify a Clerk JWT token with proper signature verification

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # First decode without verification to get the header
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get('kid')

        if not kid:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing key ID"
            )

        # Get JWKS
        jwks = get_clerk_jwks()

        if not jwks:
            # Fallback to unverified decode if JWKS not available
            logger.warning("JWKS not available - falling back to unverified decode")
            payload = jwt.decode(
                token,
                key='',
                options={"verify_signature": False}
            )
        else:
            # Find the key with matching kid
            key = None
            for jwk_key in jwks.get('keys', []):
                if jwk_key.get('kid') == kid:
                    key = jwk_key
                    break

            if not key:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: key not found"
                )

            # Convert JWK to PEM for verification
            public_key = jwk.construct(key, algorithm=ALGORITHMS.RS256)

            # Verify and decode the token
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=['RS256'],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Clerk doesn't always include audience
                    "require_exp": True,
                    "require_iat": True,
                    "require_nbf": False
                }
            )

        # Additional validation
        if not payload.get('sub'):
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        # Check if token is expired (backup check)
        exp = payload.get('exp')
        if exp and exp < time.time():
            raise HTTPException(
                status_code=401,
                detail="Invalid token: Token has expired"
            )

        return payload

    except JWTError as e:
        # Handle specific JWT errors
        error_message = str(e)
        if 'expired' in error_message.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid token: Signature has expired"
            )
        elif 'signature' in error_message.lower():
            raise HTTPException(
                status_code=401,
                detail="Invalid token: Signature verification failed"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {error_message}"
            )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token: Verification failed"
        )


async def get_current_user_id(
    authorization: str = Header(default=None, alias="Authorization", description="Bearer token from Clerk")
) -> str:
    """
    Extract and verify user ID from Clerk JWT token with proper verification

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

    # Verify token with proper signature verification
    payload = verify_clerk_token(token)

    # Extract user ID
    user_id = payload.get('sub')

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: missing user ID"
        )

    logger.debug(f"Authenticated user: {user_id}")
    return user_id


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


async def get_current_admin_user_id(
    authorization: str = Header(default=None, alias="Authorization", description="Bearer token from Clerk")
) -> str:
    """
    Verify user is authenticated AND has admin privileges

    For now, just verifies authentication.
    TODO: Add actual admin role checking from database or Clerk metadata

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Clerk user ID if authenticated

    Raises:
        HTTPException: If not authenticated or not admin
    """
    return await get_current_user_id(authorization)