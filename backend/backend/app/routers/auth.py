from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import RefreshToken, User
from app.schemas import LoginRequest, RefreshTokenRequest, SignupRequest, TokenResponse
from app.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.clients import get_redis
from app.config import settings


router = APIRouter()


@router.post("/signup", status_code=201)
async def signup(payload: SignupRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already in use")
    user = User(email=payload.email,
                password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    return {"id": str(user.id), "email": user.email}


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # rate limit and account lock checks
    redis = get_redis()
    if redis is not None and not settings.disable_rate_limiting:
        client_ip = request.client.host if request.client else "unknown"
        rl_ip_key = f"rl:login:ip:{client_ip}"
        rl_email_key = f"rl:login:email:{payload.email}"
        ip_count = await redis.incr(rl_ip_key)
        email_count = await redis.incr(rl_email_key)
        if ip_count == 1:
            await redis.expire(rl_ip_key, 60)
        if email_count == 1:
            await redis.expire(rl_email_key, 60)
        if (
            ip_count > settings.rate_limit_login_per_minute
            or email_count > settings.rate_limit_login_per_minute
        ):
            raise HTTPException(
                status_code=429, detail="Too many login attempts")
        lock_key = f"user:locked:{payload.email}"
        if await redis.ttl(lock_key) > 0:
            raise HTTPException(
                status_code=423, detail="Account temporarily locked")
    if user is None or not verify_password(payload.password, user.password_hash):
        if redis is not None and not settings.disable_rate_limiting:
            failures_key = f"user:failures:{payload.email}"
            failures = await redis.incr(failures_key)
            if failures == 1:
                await redis.expire(failures_key, settings.account_lock_minutes * 60)
            if failures >= settings.account_lock_threshold:
                await redis.setex(
                    f"user:locked:{payload.email}", settings.account_lock_minutes * 60, "1"
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = create_access_token(str(user.id))
    raw_refresh, hashed = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed))
    await db.commit()
    if redis is not None and not settings.disable_rate_limiting:
        await redis.delete(f"user:failures:{payload.email}")
    return TokenResponse(access_token=access, refresh_token=raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    hashed = hashlib.sha256(payload.token.encode()).hexdigest()
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    token_row = result.scalar_one_or_none()
    if token_row is None or token_row.revoked:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # TTL check
    from datetime import datetime, timezone, timedelta

    max_age = timedelta(days=settings.refresh_token_expire_days)
    created = token_row.created_at
    # created_at stored naive UTC; compare safely
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if created is None or (now - created) > max_age:
        token_row.revoked = True
        await db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # rotate
    token_row.revoked = True
    raw_refresh, new_hashed = create_refresh_token()
    token_row.replaced_by = new_hashed
    db.add(RefreshToken(user_id=token_row.user_id, token_hash=new_hashed))
    await db.commit()

    access = create_access_token(str(token_row.user_id))
    return TokenResponse(access_token=access, refresh_token=raw_refresh)


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """Revoke the provided refresh token (logout)."""
    hashed = hashlib.sha256(payload.token.encode()).hexdigest()
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    token_row = result.scalar_one_or_none()
    if token_row is None:
        # Return 200 to avoid information leakage
        return {"status": "ok"}
    token_row.revoked = True
    await db.commit()
    return {"status": "ok"}
