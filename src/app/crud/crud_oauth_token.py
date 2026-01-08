from fastcrud import FastCRUD

from ..models.oauth_token import OAuthToken
from ..schemas.oauth_token import (
    OAuthTokenCreateInternal,
    OAuthTokenRead,
    OAuthTokenUpdate,
    OAuthTokenUpdateInternal,
)

CRUDOAuthToken = FastCRUD[
    OAuthToken, OAuthTokenCreateInternal, OAuthTokenUpdate, OAuthTokenUpdateInternal, OAuthTokenRead, OAuthTokenRead
]
crud_oauth_token = CRUDOAuthToken(OAuthToken)
