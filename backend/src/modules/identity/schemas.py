"""Pydantic I/O — camelCase over the wire, snake_case inside."""

from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from src.core.config import settings
from src.core.schemas import CamelModel


class SignupRequest(CamelModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str
    confirm_password: str
    accept_terms: bool

    @field_validator("password")
    @classmethod
    def _password_min_length(cls, value: str) -> str:
        if len(value) < settings.auth.password_min_length:
            raise ValueError(
                f"Password must be at least {settings.auth.password_min_length} characters."
            )
        return value

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the Privacy Policy and Terms of Service.")
        return value

    @field_validator("confirm_password")
    @classmethod
    def _matches(cls, value: str, info):  # type: ignore[no-untyped-def]
        if info.data.get("password") != value:
            raise ValueError("Passwords do not match.")
        return value


class SignupResponse(CamelModel):
    user_id: UUID
    email: EmailStr
    activation_sent: bool


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class TokenResponse(CamelModel):
    access_token: str
    expires_in: int


class ActivateRequest(CamelModel):
    token: str


class ResendActivationRequest(CamelModel):
    email: EmailStr


class ResendActivationResponse(CamelModel):
    sent: bool
    cooldown_remaining_seconds: int


class ForgotPasswordRequest(CamelModel):
    email: EmailStr


class ResetPasswordRequest(CamelModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _len(cls, value: str) -> str:
        if len(value) < settings.auth.password_min_length:
            raise ValueError(
                f"Password must be at least {settings.auth.password_min_length} characters."
            )
        return value


class MeResponse(CamelModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    email_verified: bool
    roles: list[str]
    tenant_id: UUID


class ChangePasswordRequest(CamelModel):
    current_password: str
    new_password: str


class StaffMember(CamelModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    roles: list[str]
    email_verified: bool


class StaffInviteRequest(CamelModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    roles: list[str] = Field(min_length=1)


class StaffRolesUpdate(CamelModel):
    roles: list[str] = Field(min_length=1)
