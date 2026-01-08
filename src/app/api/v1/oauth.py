"""OAuth2 authentication endpoints for Google."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import BadRequestException
from ...core.oauth2 import (
    exchange_code_for_token,
    get_authorization_url,
    get_user_info,
    revoke_oauth_token,
    save_oauth_token,
)
from ...core.security import create_access_token, create_refresh_token
from ...crud.crud_users import crud_users
from ..dependencies import get_current_user

router = APIRouter(tags=["oauth"])


@router.get("/auth/google")
async def google_login() -> dict[str, str]:
    """Initiate Google OAuth2 flow.

    Returns
    -------
    dict[str, str]
        Authorization URL to redirect user to Google login
    """
    authorization_url, state = await get_authorization_url()
    return {"authorization_url": authorization_url, "state": state}


@router.get("/auth/callback")
async def google_callback(
    response: Response,
    code: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    """Handle Google OAuth2 callback and create/login user.

    Parameters
    ----------
    response: Response
        FastAPI response to set cookies
    code: str
        Authorization code from Google
    db: AsyncSession
        Database session

    Returns
    -------
    dict[str, str]
        Access token for the authenticated user
    """
    if not code:
        raise BadRequestException("Authorization code missing.")

    # Exchange code for tokens
    token_data = await exchange_code_for_token(code)

    # Get user info from Google
    user_info = await get_user_info(token_data["access_token"])

    # Check if user exists
    oauth_sub = user_info["id"]
    email = user_info["email"]

    db_user = await crud_users.get(db=db, email=email, is_deleted=False)

    if not db_user:
        # Create new user
        from ...schemas.user import UserCreateInternal

        username = email.split("@")[0]
        # Ensure username is unique
        existing_username = await crud_users.get(db=db, username=username)
        if existing_username:
            username = f"{username}_{oauth_sub[:8]}"

        user_create = UserCreateInternal(
            name=user_info.get("name", username),
            username=username,
            email=email,
            hashed_password="",  # No password for OAuth users
            profile_image_url=user_info.get("picture", "https://profileimageurl.com"),
        )
        db_user = await crud_users.create(db=db, object=user_create)

    # Update user with OAuth provider info
    from ...schemas.user import UserUpdateInternal

    user_update = UserUpdateInternal(oauth_provider="google", oauth_sub=oauth_sub)  # type: ignore[call-arg]
    db_user = await crud_users.update(db=db, object=user_update, id=db_user["id"])

    # Save OAuth tokens
    await save_oauth_token(db, db_user["id"], token_data)

    # Create JWT tokens for the user
    access_token = await create_access_token(data={"sub": db_user["username"]})
    refresh_token = await create_refresh_token(data={"sub": db_user["username"]})

    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=max_age
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/link-google")
async def link_google_account(
    code: Annotated[str, Query()],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    """Link Google account to existing authenticated user.

    Parameters
    ----------
    code: str
        Authorization code from Google
    current_user: dict
        Currently authenticated user
    db: AsyncSession
        Database session

    Returns
    -------
    dict[str, str]
        Success message
    """
    if not code:
        raise BadRequestException("Authorization code missing.")

    # Exchange code for tokens
    token_data = await exchange_code_for_token(code)

    # Get user info from Google
    user_info = await get_user_info(token_data["access_token"])
    oauth_sub = user_info["id"]

    # Update user with OAuth provider info
    from ...schemas.user import UserUpdateInternal

    user_update = UserUpdateInternal(oauth_provider="google", oauth_sub=oauth_sub)  # type: ignore[call-arg]
    await crud_users.update(db=db, object=user_update, id=current_user["id"])

    # Save OAuth tokens
    await save_oauth_token(db, current_user["id"], token_data)

    return {"message": "Google account linked successfully"}


@router.post("/auth/unlink-google")
async def unlink_google_account(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    """Unlink Google account from authenticated user.

    Parameters
    ----------
    current_user: dict
        Currently authenticated user
    db: AsyncSession
        Database session

    Returns
    -------
    dict[str, str]
        Success message
    """
    # Check if user has password set (can't unlink if OAuth is only auth method)
    if not current_user.get("hashed_password"):
        raise BadRequestException("Cannot unlink Google account. Please set a password first.")

    # Revoke OAuth token
    success = await revoke_oauth_token(db, current_user["id"], "google")

    if not success:
        raise BadRequestException("No Google account linked.")

    # Remove OAuth fields from user
    from ...schemas.user import UserUpdateInternal

    user_update = UserUpdateInternal(oauth_provider=None, oauth_sub=None)  # type: ignore[call-arg]
    await crud_users.update(db=db, object=user_update, id=current_user["id"])

    return {"message": "Google account unlinked successfully"}
