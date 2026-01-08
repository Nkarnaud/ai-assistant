"""OAuth2 service for Google authentication and token management."""

from datetime import UTC, datetime, timedelta
from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.oauth_token import OAuthToken
from ..schemas.oauth_token import OAuthTokenCreateInternal, OAuthTokenUpdateInternal
from .config import settings
from .security import decrypt_token, encrypt_token

# Google OAuth2 endpoints
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def get_authorization_url() -> tuple[str, str]:
    """Generate Google OAuth2 authorization URL.

    Returns
    -------
    tuple[str, str]
        A tuple containing (authorization_url, state)
    """
    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope=" ".join(settings.OAUTH2_SCOPES),
    )
    authorization_url, state = client.create_authorization_url(GOOGLE_AUTHORIZATION_URL, access_type="offline")
    return authorization_url, state


async def exchange_code_for_token(code: str) -> dict[str, Any]:
    """Exchange authorization code for access and refresh tokens.

    Parameters
    ----------
    code: str
        Authorization code from Google OAuth callback

    Returns
    -------
    dict[str, Any]
        Token response containing access_token, refresh_token, expires_in, etc.
    """
    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    token = await client.fetch_token(GOOGLE_TOKEN_URL, code=code, grant_type="authorization_code")
    return token


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Refresh an expired access token using refresh token.

    Parameters
    ----------
    refresh_token: str
        The encrypted refresh token from database

    Returns
    -------
    dict[str, Any]
        New token response with fresh access_token
    """
    decrypted_refresh_token = decrypt_token(refresh_token)

    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET.get_secret_value(),
    )
    token = await client.refresh_token(GOOGLE_TOKEN_URL, refresh_token=decrypted_refresh_token)
    return token


async def get_user_info(access_token: str) -> dict[str, Any]:
    """Get user info from Google using access token.

    Parameters
    ----------
    access_token: str
        Google OAuth2 access token

    Returns
    -------
    dict[str, Any]
        User info including id (sub), email, name, picture, etc.
    """
    client = AsyncOAuth2Client(token={"access_token": access_token, "token_type": "Bearer"})
    response = await client.get(GOOGLE_USERINFO_URL)
    response.raise_for_status()
    return response.json()


async def save_oauth_token(db: AsyncSession, user_id: int, token_data: dict[str, Any]) -> OAuthToken:
    """Save or update OAuth token in database with encryption.

    Parameters
    ----------
    db: AsyncSession
        Database session
    user_id: int
        User ID to associate token with
    token_data: dict[str, Any]
        Token data from Google OAuth response

    Returns
    -------
    OAuthToken
        The saved OAuth token record
    """
    from ..crud.crud_oauth_token import crud_oauth_token

    # Encrypt sensitive tokens
    encrypted_access_token = encrypt_token(token_data["access_token"])
    encrypted_refresh_token = encrypt_token(token_data["refresh_token"]) if token_data.get("refresh_token") else None

    # Calculate expiration time
    expires_in = token_data.get("expires_in", 3600)
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    # Check if token already exists for this user and provider
    existing_token = await crud_oauth_token.get(db=db, user_id=user_id, provider="google")

    if existing_token:
        # Update existing token
        update_data = OAuthTokenUpdateInternal(
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if isinstance(token_data.get("scope"), str) else [],
            updated_at=datetime.now(UTC),
        )
        updated_token = await crud_oauth_token.update(db=db, object=update_data, id=existing_token["id"])
        return updated_token
    else:
        # Create new token
        create_data = OAuthTokenCreateInternal(
            user_id=user_id,
            provider="google",
            access_token=encrypted_access_token,
            refresh_token=encrypted_refresh_token,
            token_type=token_data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scopes=token_data.get("scope", "").split() if isinstance(token_data.get("scope"), str) else [],
        )
        new_token = await crud_oauth_token.create(db=db, object=create_data)
        return new_token


async def get_valid_access_token(db: AsyncSession, user_id: int, provider: str = "google") -> str | None:
    """Get a valid access token for a user, refreshing if necessary.

    Parameters
    ----------
    db: AsyncSession
        Database session
    user_id: int
        User ID
    provider: str
        OAuth provider (default: "google")

    Returns
    -------
    str | None
        Valid decrypted access token, or None if no token exists
    """
    from ..crud.crud_oauth_token import crud_oauth_token

    token_record = await crud_oauth_token.get(db=db, user_id=user_id, provider=provider)

    if not token_record:
        return None

    # Check if token is expired
    now = datetime.now(UTC)
    if token_record["expires_at"] <= now:
        # Token expired, refresh it
        if not token_record["refresh_token"]:
            return None

        try:
            new_token_data = await refresh_access_token(token_record["refresh_token"])
            await save_oauth_token(db, user_id, new_token_data)
            return new_token_data["access_token"]
        except Exception:
            return None

    # Token is still valid, decrypt and return
    return decrypt_token(token_record["access_token"])


async def revoke_oauth_token(db: AsyncSession, user_id: int, provider: str = "google") -> bool:
    """Revoke and delete OAuth token for a user.

    Parameters
    ----------
    db: AsyncSession
        Database session
    user_id: int
        User ID
    provider: str
        OAuth provider (default: "google")

    Returns
    -------
    bool
        True if token was deleted, False if no token found
    """
    from ..crud.crud_oauth_token import crud_oauth_token

    token_record = await crud_oauth_token.get(db=db, user_id=user_id, provider=provider)

    if not token_record:
        return False

    await crud_oauth_token.delete(db=db, db_row=token_record)
    return True
