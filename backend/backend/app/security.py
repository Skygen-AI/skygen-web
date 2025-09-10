from __future__ import annotations

import hashlib
import json
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Tuple

import jwt
from passlib.context import CryptContext

from app.config import settings
from app.clients import get_redis


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(sub: str) -> str:
    exp = now_utc() + timedelta(minutes=settings.access_token_expire_minutes)
    jti = uuid.uuid4().hex
    payload = {"sub": sub, "exp": exp, "jti": jti}
    return jwt.encode(payload, settings.access_token_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    # type: ignore[no-any-return]
    return jwt.decode(token, settings.access_token_secret, algorithms=["HS256"])


def create_refresh_token() -> Tuple[str, str]:
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def create_device_token(device_id: str) -> Tuple[str, str, str]:
    keys = settings.device_jwt_keys
    kid = keys.active_kid
    secret = keys.keys[kid]
    exp = now_utc() + timedelta(hours=24)
    jti = uuid.uuid4().hex
    payload = {"device_id": device_id, "jti": jti, "exp": exp, "iat": now_utc()}
    headers = {"kid": kid}
    token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
    return token, jti, kid


def verify_device_token(token: str) -> dict[str, Any]:
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    if kid is None:
        raise jwt.InvalidTokenError("Missing kid")
    secret = settings.device_jwt_keys.keys.get(kid)
    if secret is None:
        raise jwt.InvalidTokenError("Unknown kid")
    # type: ignore[no-any-return]
    return jwt.decode(token, secret, algorithms=["HS256"])


async def store_active_device_token(device_id: str, jti: str) -> None:
    redis = get_redis()
    if redis is None:
        return
    await redis.sadd(f"device:{device_id}:active_jti", jti)


async def revoke_device_token(device_id: str, jti: str) -> None:
    redis = get_redis()
    if redis is None:
        return
    await redis.srem(f"device:{device_id}:active_jti", jti)
    await redis.sadd("revoked_device_jti", jti)


async def is_jti_revoked(jti: str) -> bool:
    redis = get_redis()
    if redis is None:
        return False
    return bool(await redis.sismember("revoked_device_jti", jti))


async def list_active_device_jtis(device_id: str) -> list[str]:
    redis = get_redis()
    if redis is None:
        return []
    members = await redis.smembers(f"device:{device_id}:active_jti")
    return list(members) if members else []


async def revoke_all_device_tokens(device_id: str) -> int:
    redis = get_redis()
    if redis is None:
        return 0
    jtis = await redis.smembers(f"device:{device_id}:active_jti")
    count = 0
    if jtis:
        for j in jtis:
            await redis.sadd("revoked_device_jti", j)
            count += 1
        await redis.delete(f"device:{device_id}:active_jti")
    return count


def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def sign_message_hmac(payload: dict[str, Any]) -> str:
    """Compute HMAC-SHA256 signature over canonical JSON of payload using active device key.

    This is used to sign server->device task envelopes and device->server results.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    keys = settings.device_jwt_keys
    secret = keys.keys[keys.active_kid]
    digest = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return digest


def verify_message_hmac(payload: dict[str, Any], signature: str) -> bool:
    expected = sign_message_hmac(payload)
    return hmac.compare_digest(expected, signature)
