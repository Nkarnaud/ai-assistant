from fastcrud import FastCRUD

from ..models.notification_preference import NotificationPreference
from ..schemas.notification_preference import (
    NotificationPreferenceCreateInternal,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationPreferenceUpdateInternal,
)

CRUDNotificationPreference = FastCRUD[
    NotificationPreference,
    NotificationPreferenceCreateInternal,
    NotificationPreferenceUpdate,
    NotificationPreferenceUpdateInternal,
    NotificationPreferenceRead,
    NotificationPreferenceRead,
]
crud_notification_preferences = CRUDNotificationPreference(NotificationPreference)
