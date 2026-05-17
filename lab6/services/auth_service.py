import uuid
from typing import Optional

from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from repository import user_repository
from schemas.user import UserRegister

_active_refresh_tokens: set[str] = set()


async def register(db: AsyncSession, data: UserRegister) -> Optional[object]:
    if await user_repository.get_by_username(db, data.username):
        return None
    return await user_repository.create(db, {
        "id": str(uuid.uuid4()),
        "username": data.username,
        "hashed_password": hash_password(data.password),
        "is_active": True,
    })


async def login(db: AsyncSession, username: str, password: str) -> Optional[dict]:
    user = await user_repository.get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    access = create_access_token(user.id, user.username)
    refresh = create_refresh_token(user.id)
    _active_refresh_tokens.add(refresh)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


async def refresh(db: AsyncSession, token: str) -> Optional[dict]:
    if token not in _active_refresh_tokens:
        return None
    try:
        payload = decode_token(token)
        if payload.get("kind") != "refresh":
            return None
        user_id = payload["uid"]
    except InvalidTokenError:
        _active_refresh_tokens.discard(token)
        return None

    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        _active_refresh_tokens.discard(token)
        return None

    _active_refresh_tokens.discard(token)
    new_access = create_access_token(user.id, user.username)
    new_refresh = create_refresh_token(user.id)
    _active_refresh_tokens.add(new_refresh)
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


def logout(token: str) -> None:
    _active_refresh_tokens.discard(token)


def clear_refresh_tokens() -> None:
    _active_refresh_tokens.clear()
