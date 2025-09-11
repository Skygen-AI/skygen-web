from __future__ import annotations
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re
from typing import Any, Literal
import uuid as _uuid


class SignupRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        # Enforce stricter email policy than RFC to block edge/malicious inputs
        s = str(v)
        if len(s) > 254:
            raise ValueError("Email too long")
        # Disallow spaces and consecutive dots
        if " " in s or ".." in s:
            raise ValueError("Invalid email format")
        # Simple safe pattern for common emails
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.fullmatch(pattern, s):
            raise ValueError("Invalid email format")
        # Disallow dot at start/end of local or domain parts
        local, domain = s.split("@", 1)
        if local.startswith(".") or local.endswith("."):
            raise ValueError("Invalid email format")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("Invalid email format")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        # Mirror signup email restrictions
        s = str(v)
        if len(s) > 254:
            raise ValueError("Email too long")
        if " " in s or ".." in s:
            raise ValueError("Invalid email format")
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if not re.fullmatch(pattern, s):
            raise ValueError("Invalid email format")
        local, domain = s.split("@", 1)
        if local.startswith(".") or local.endswith("."):
            raise ValueError("Invalid email format")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("Invalid email format")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    token: str


class DeviceEnrollRequest(BaseModel):
    device_name: str
    platform: str
    capabilities: dict = Field(default_factory=dict)
    idempotency_key: str | None = None

    @field_validator("device_name")
    @classmethod
    def validate_device_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Device name cannot be empty")
        return v


class DeviceEnrollResponse(BaseModel):
    device_id: _uuid.UUID
    device_token: str
    wss_url: str
    kid: str
    expires_at: datetime


class DeviceTokenRefreshRequest(BaseModel):
    device_id: _uuid.UUID


class DeviceRevokeResponse(BaseModel):
    device_id: _uuid.UUID
    revoked_count: int


class TaskCreateRequest(BaseModel):
    device_id: _uuid.UUID
    title: str
    description: str | None = None
    metadata: dict[str, Any] | None = None


class TaskResponse(BaseModel):
    id: str
    user_id: _uuid.UUID
    device_id: _uuid.UUID
    status: Literal[
        "created",
        "queued",
        "assigned",
        "in_progress",
        "awaiting_confirmation",
        "completed",
        "failed",
        "cancelled",
    ]
    title: str
    description: str | None = None
    payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ArtifactPresignRequest(BaseModel):
    task_id: str
    filename: str
    size: int = Field(gt=0, description="File size must be positive")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v


# Chat Schemas
class ChatSessionCreate(BaseModel):
    title: str = Field(max_length=255)
    device_id: _uuid.UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatSessionResponse(BaseModel):
    id: _uuid.UUID
    user_id: _uuid.UUID
    device_id: _uuid.UUID | None
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    metadata: dict[str, Any] = Field(alias="meta_data")
    message_count: int = 0

    model_config = ConfigDict(populate_by_name=True)


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    role: Literal["user", "assistant", "system"] = "user"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    id: _uuid.UUID
    session_id: _uuid.UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(alias="meta_data")
    task_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionWithMessages(BaseModel):
    id: _uuid.UUID
    user_id: _uuid.UUID
    device_id: _uuid.UUID | None
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    metadata: dict[str, Any] = Field(alias="meta_data")
    messages: list[ChatMessageResponse]

    model_config = ConfigDict(populate_by_name=True)


# Agent API Schemas
class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: _uuid.UUID | None = None
    device_id: _uuid.UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentChatResponse(BaseModel):
    session_id: _uuid.UUID
    message: ChatMessageResponse
    assistant_message: ChatMessageResponse | None = None
    task_created: bool = False
    task_id: str | None = None
