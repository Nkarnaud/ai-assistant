"""API endpoints for managing draft email replies."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user, get_google_credentials
from ...core.db.database import async_get_db
from ...crud.crud_draft_reply import crud_draft_replies
from ...crud.crud_email_message import crud_email_messages
from ...models.draft_reply import DraftStatus
from ...schemas.draft_reply import (
    DraftReplyApprove,
    DraftReplyRead,
    DraftReplyReject,
    DraftReplyUpdate,
    DraftReplyUpdateInternal,
    DraftReplyWithEmail,
)
from ...services.gmail_service import GmailService

router = APIRouter(tags=["drafts"])


@router.get("/drafts", response_model=dict)
async def list_drafts(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """List draft replies for current user.

    Parameters
    ----------
    current_user: dict
        Current authenticated user
    db: AsyncSession
        Database session
    status: str | None
        Filter by status (pending, approved, rejected, edited)
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return

    Returns
    -------
    dict
        Paginated list of drafts
    """
    filters = {"user_id": current_user["id"]}
    if status:
        filters["status"] = status

    drafts = await crud_draft_replies.get_multi(db=db, offset=skip, limit=limit, **filters)

    # Enrich with email details
    enriched_drafts = []
    for draft in drafts.get("data", []):
        email = await crud_email_messages.get(db=db, id=draft["email_message_id"])
        if email:
            enriched_draft = {
                **draft,
                "email_subject": email.get("subject", ""),
                "email_from": email.get("from_email", ""),
                "email_received_at": email.get("received_at"),
                "email_snippet": email.get("snippet"),
            }
            enriched_drafts.append(enriched_draft)

    return {"data": enriched_drafts, "total": drafts.get("total_count", 0)}


@router.get("/drafts/{draft_id}", response_model=DraftReplyWithEmail)
async def get_draft(
    draft_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Get specific draft reply with email context.

    Parameters
    ----------
    draft_id: int
        Draft reply ID
    current_user: dict
        Current authenticated user
    db: AsyncSession
        Database session

    Returns
    -------
    dict
        Draft with email details
    """
    draft = await crud_draft_replies.get(db=db, id=draft_id, user_id=current_user["id"])

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Get associated email
    email = await crud_email_messages.get(db=db, id=draft["email_message_id"])

    if not email:
        raise HTTPException(status_code=404, detail="Associated email not found")

    return {
        **draft,
        "email_subject": email.get("subject", ""),
        "email_from": email.get("from_email", ""),
        "email_received_at": email.get("received_at"),
        "email_snippet": email.get("snippet"),
    }


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(
    draft_id: int,
    approval_data: DraftReplyApprove,
    current_user: Annotated[dict, Depends(get_current_user)],
    google_credentials: Annotated[str, Depends(get_google_credentials)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Approve and send a draft reply.

    Parameters
    ----------
    draft_id: int
        Draft reply ID
    approval_data: DraftReplyApprove
        Approval data (optional edits)
    current_user: dict
        Current authenticated user
    google_credentials: str
        Valid Google OAuth token
    db: AsyncSession
        Database session

    Returns
    -------
    dict
        Success response
    """
    draft = await crud_draft_replies.get(db=db, id=draft_id, user_id=current_user["id"])

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft["status"] != DraftStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Draft already {draft['status']}")

    # Get associated email
    email = await crud_email_messages.get(db=db, id=draft["email_message_id"])
    if not email:
        raise HTTPException(status_code=404, detail="Associated email not found")

    # Use edited content if provided
    final_content = approval_data.edited_content if approval_data.edited_content else draft["draft_content"]

    # Send email via Gmail
    gmail_service = GmailService(google_credentials)

    try:
        await gmail_service.send_message(to=email["from_email"], subject=f"Re: {email['subject']}", body=final_content)

        # Update draft status
        status = DraftStatus.EDITED.value if approval_data.edited_content else DraftStatus.APPROVED.value

        await crud_draft_replies.update(
            db=db,
            object=DraftReplyUpdateInternal(
                draft_content=final_content if approval_data.edited_content else None,
                status=status,
                reviewed_at=datetime.now(UTC),
                sent_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            id=draft_id,
        )

        return {"message": "Draft sent successfully", "draft_id": draft_id, "status": status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/drafts/{draft_id}/reject")
async def reject_draft(
    draft_id: int,
    rejection_data: DraftReplyReject,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    """Reject a draft reply.

    Parameters
    ----------
    draft_id: int
        Draft reply ID
    rejection_data: DraftReplyReject
        Rejection reason
    current_user: dict
        Current authenticated user
    db: AsyncSession
        Database session

    Returns
    -------
    dict
        Success response
    """
    draft = await crud_draft_replies.get(db=db, id=draft_id, user_id=current_user["id"])

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft["status"] != DraftStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Draft already {draft['status']}")

    # Update draft status
    await crud_draft_replies.update(
        db=db,
        object=DraftReplyUpdateInternal(
            status=DraftStatus.REJECTED.value,
            rejection_reason=rejection_data.rejection_reason,
            reviewed_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        id=draft_id,
    )

    return {"message": "Draft rejected", "draft_id": draft_id}


@router.put("/drafts/{draft_id}")
async def edit_draft(
    draft_id: int,
    draft_update: DraftReplyUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> DraftReplyRead:
    """Edit a draft reply (content only, not status).

    Parameters
    ----------
    draft_id: int
        Draft reply ID
    draft_update: DraftReplyUpdate
        Updated draft content
    current_user: dict
        Current authenticated user
    db: AsyncSession
        Database session

    Returns
    -------
    DraftReplyRead
        Updated draft
    """
    draft = await crud_draft_replies.get(db=db, id=draft_id, user_id=current_user["id"])

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft["status"] != DraftStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Can only edit pending drafts")

    # Update draft
    updated = await crud_draft_replies.update(
        db=db,
        object=DraftReplyUpdateInternal(draft_content=draft_update.draft_content, updated_at=datetime.now(UTC)),
        id=draft_id,
    )

    return updated
