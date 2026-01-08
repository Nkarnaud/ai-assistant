from fastcrud import FastCRUD

from ..models.email_message import EmailMessage
from ..schemas.email_message import (
    EmailMessageCreateInternal,
    EmailMessageRead,
    EmailMessageUpdate,
    EmailMessageUpdateInternal,
)

CRUDEmailMessage = FastCRUD[
    EmailMessage,
    EmailMessageCreateInternal,
    EmailMessageUpdate,
    EmailMessageUpdateInternal,
    EmailMessageRead,
    EmailMessageRead,
]
crud_email_messages = CRUDEmailMessage(EmailMessage)
