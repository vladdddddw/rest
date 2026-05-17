from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import UserRegister, UserOut
from schemas.token import LoginRequest, TokenResponse, RefreshRequest
from services import auth_service
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(db, data)
    if user is None:
        raise HTTPException(status_code=409, detail="Username already taken")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.login(db, data.username, data.password)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await auth_service.refresh(db, data.refresh_token)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Token is invalid or has expired")
    return tokens


@router.post("/logout")
async def logout(data: RefreshRequest):
    auth_service.logout(data.refresh_token)
    return {"message": "Logged out"}
