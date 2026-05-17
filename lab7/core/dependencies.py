from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError

from core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("kind") != "access":
            return None
        return {"id": payload["uid"], "username": payload["username"]}
    except InvalidTokenError:
        return None


def get_current_user(
    current_user: Optional[dict] = Depends(get_optional_user),
) -> dict:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    return current_user
