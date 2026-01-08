from fastapi import APIRouter

from .calendar import router as calendar_router
from .drafts import router as drafts_router
from .emails import router as emails_router
from .gmail import router as gmail_router
from .health import router as health_router
from .login import router as login_router
from .logout import router as logout_router
from .notifications import router as notifications_router
from .oauth import router as oauth_router
from .users import router as users_router
from .webhooks import router as webhooks_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(oauth_router)
router.include_router(users_router)
router.include_router(gmail_router)
router.include_router(emails_router)
router.include_router(drafts_router)
router.include_router(calendar_router)
router.include_router(notifications_router)
router.include_router(webhooks_router)
