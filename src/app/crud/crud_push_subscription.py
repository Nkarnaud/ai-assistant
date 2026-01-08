from fastcrud import FastCRUD

from ..models.push_subscription import PushSubscription
from ..schemas.push_subscription import (
    PushSubscriptionCreateInternal,
    PushSubscriptionRead,
    PushSubscriptionUpdate,
    PushSubscriptionUpdateInternal,
)

CRUDPushSubscription = FastCRUD[
    PushSubscription,
    PushSubscriptionCreateInternal,
    PushSubscriptionUpdate,
    PushSubscriptionUpdateInternal,
    PushSubscriptionRead,
    PushSubscriptionRead,
]
crud_push_subscriptions = CRUDPushSubscription(PushSubscription)
