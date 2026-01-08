"""API endpoints for email management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.db.database import async_get_db
from ...crud.crud_email_message import crud_email_messages
from ...schemas.email_message import EmailMessageRead

router = APIRouter(tags=["emails"])


@router.get("/emails", response_model=dict)
async def list_emails(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    classification: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    """List processed emails for current user."""
    filters = {"user_id": current_user["id"]}
    if classification:
        filters["classification"] = classification

    emails = await crud_email_messages.get_multi(db=db, offset=skip, limit=limit, **filters)
    return emails


@router.get("/emails/{email_id}", response_model=EmailMessageRead)
async def get_email(
    email_id: int, current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict:
    """Get specific email details."""
    email = await crud_email_messages.get(db=db, id=email_id, user_id=current_user["id"])
    if not email:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Email not found")
    return email
