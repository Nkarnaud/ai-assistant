from fastcrud import FastCRUD

from ..models.draft_reply import DraftReply
from ..schemas.draft_reply import (
    DraftReplyCreate,
    DraftReplyCreateInternal,
    DraftReplyRead,
    DraftReplyUpdate,
    DraftReplyUpdateInternal,
)

CRUDDraftReply = FastCRUD[
    DraftReply, DraftReplyCreateInternal, DraftReplyUpdate, DraftReplyUpdateInternal, DraftReplyRead, DraftReplyRead
]
crud_draft_replies = CRUDDraftReply(DraftReply)
