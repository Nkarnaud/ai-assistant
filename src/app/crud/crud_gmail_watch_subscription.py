from fastcrud import FastCRUD

from ..models.gmail_watch_subscription import GmailWatchSubscription
from ..schemas.gmail_watch_subscription import (
    GmailWatchSubscriptionCreateInternal,
    GmailWatchSubscriptionRead,
    GmailWatchSubscriptionUpdate,
    GmailWatchSubscriptionUpdateInternal,
)

CRUDGmailWatchSubscription = FastCRUD[
    GmailWatchSubscription,
    GmailWatchSubscriptionCreateInternal,
    GmailWatchSubscriptionUpdate,
    GmailWatchSubscriptionUpdateInternal,
    GmailWatchSubscriptionRead,
    GmailWatchSubscriptionRead,
]
crud_gmail_watch_subscriptions = CRUDGmailWatchSubscription(GmailWatchSubscription)
