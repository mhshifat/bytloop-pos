"""Identity HTTP endpoints — thin layer over ``IdentityService``."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from src.core import cache
from src.core.config import settings
from src.core.deps import (
    DbSession,
    REFRESH_COOKIE_NAME,
    get_current_user,
    refresh_cookie,
    requires,
)
from src.core.permissions import Permission
from src.integrations.email.factory import get_email_adapter
from src.modules.identity.repository import UserRepository
from src.modules.identity.schemas import (
    ActivateRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    ResendActivationRequest,
    ResendActivationResponse,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    StaffInviteRequest,
    StaffMember,
    StaffRolesUpdate,
    TokenResponse,
)
from src.modules.identity.service import IdentityService, LoginTokens

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(db: DbSession) -> IdentityService:
    return IdentityService(db, email=get_email_adapter())


def _set_refresh_cookie(response: Response, tokens: LoginTokens) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        tokens.refresh_token,
        max_age=tokens.refresh_ttl_seconds,
        httponly=True,
        secure=settings.app.env == "production",
        samesite="lax",
        path="/",
    )

def _client_ip(request: Request) -> str:
    # Filled by RealIpMiddleware. Fall back defensively.
    ip = getattr(request.state, "real_ip", None)
    if isinstance(ip, str) and ip:
        return ip
    return request.client.host if request.client else "unknown"


async def _rate_limit_ok(*, key: str, limit: int, window_seconds: int) -> bool:
    """Fixed-window counter. Redis down => fail open."""
    current_raw = await cache.get_str(key)
    if current_raw is None:
        await cache.set_str(key, "1", ttl_seconds=window_seconds)
        return True
    count = int(current_raw) if current_raw.isdigit() else 0
    if count >= limit:
        return False
    await cache.set_str(key, str(count + 1), ttl_seconds=window_seconds)
    return True


async def _enforce_rate_limits_login(request: Request, email: str) -> None:
    from src.core.errors import RateLimitError

    ip = _client_ip(request)
    if not await _rate_limit_ok(key=f"pos:rl:auth:login:ip:{ip}", limit=20, window_seconds=60):
        raise RateLimitError("Too many login attempts. Please wait a moment.")
    if not await _rate_limit_ok(
        key=f"pos:rl:auth:login:email:{email.lower()}",
        limit=12,
        window_seconds=300,
    ):
        raise RateLimitError("Too many login attempts. Please wait a few minutes.")


async def _enforce_rate_limits_forgot(request: Request, email: str) -> None:
    from src.core.errors import RateLimitError

    ip = _client_ip(request)
    if not await _rate_limit_ok(key=f"pos:rl:auth:forgot:ip:{ip}", limit=10, window_seconds=60):
        raise RateLimitError("Too many requests. Please wait a moment.")
    if not await _rate_limit_ok(
        key=f"pos:rl:auth:forgot:email:{email.lower()}",
        limit=3,
        window_seconds=900,
    ):
        raise RateLimitError("Too many requests. Please wait a few minutes.")


async def _enforce_rate_limits_reset(request: Request, token: str) -> None:
    from src.core.errors import RateLimitError

    ip = _client_ip(request)
    if not await _rate_limit_ok(key=f"pos:rl:auth:reset:ip:{ip}", limit=20, window_seconds=60):
        raise RateLimitError("Too many requests. Please wait a moment.")
    if not await _rate_limit_ok(
        key=f"pos:rl:auth:reset:token:{token[:32]}",
        limit=10,
        window_seconds=900,
    ):
        raise RateLimitError("Too many reset attempts. Please wait a few minutes.")


async def _enforce_rate_limits_signup(request: Request, email: str) -> None:
    from src.core.errors import RateLimitError

    ip = _client_ip(request)
    # 5/min per IP + 3/30min per email
    if not await _rate_limit_ok(key=f"pos:rl:auth:signup:ip:{ip}", limit=5, window_seconds=60):
        raise RateLimitError("Too many signup attempts. Please wait a moment.")
    if not await _rate_limit_ok(
        key=f"pos:rl:auth:signup:email:{email.lower()}",
        limit=3,
        window_seconds=1800,
    ):
        raise RateLimitError("Too many signup attempts. Please wait a while.")


async def _enforce_rate_limits_resend_activation(request: Request, email: str) -> None:
    from src.core.errors import RateLimitError

    ip = _client_ip(request)
    # 10/15min per IP (service already enforces per-email cooldown)
    if not await _rate_limit_ok(
        key=f"pos:rl:auth:resend_activation:ip:{ip}",
        limit=10,
        window_seconds=900,
    ):
        raise RateLimitError("Too many requests. Please wait a few minutes.")


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, db: DbSession, request: Request) -> SignupResponse:
    await _enforce_rate_limits_signup(request, req.email)
    service = _build_service(db)
    user = await service.signup(
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        password=req.password,
    )
    return SignupResponse(user_id=user.id, email=user.email, activation_sent=True)


@router.post("/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate(req: ActivateRequest, db: DbSession) -> Response:
    await _build_service(db).activate(token=req.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/resend-activation", response_model=ResendActivationResponse)
async def resend_activation(
    req: ResendActivationRequest, db: DbSession, request: Request
) -> ResendActivationResponse:
    await _enforce_rate_limits_resend_activation(request, req.email)
    await _build_service(db).resend_activation(email=req.email)
    return ResendActivationResponse(sent=True, cooldown_remaining_seconds=0)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest, db: DbSession, response: Response, request: Request
) -> TokenResponse:
    await _enforce_rate_limits_login(request, req.email)
    tokens = await _build_service(db).login_with_password(
        email=req.email, password=req.password
    )
    _set_refresh_cookie(response, tokens)
    return TokenResponse(
        access_token=tokens.access_token, expires_in=tokens.access_ttl_seconds
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    db: DbSession,
    response: Response,
    token: Annotated[str, Depends(refresh_cookie)],
) -> TokenResponse:
    tokens = await _build_service(db).refresh(refresh_token=token)
    _set_refresh_cookie(response, tokens)
    return TokenResponse(
        access_token=tokens.access_token, expires_in=tokens.access_ttl_seconds
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    req: ForgotPasswordRequest, db: DbSession, request: Request
) -> Response:
    await _enforce_rate_limits_forgot(request, req.email)
    await _build_service(db).send_password_reset(email=req.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    req: ResetPasswordRequest, db: DbSession, request: Request
) -> Response:
    await _enforce_rate_limits_reset(request, req.token)
    await _build_service(db).reset_password(token=req.token, new_password=req.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
async def me(user=Depends(get_current_user)) -> MeResponse:  # type: ignore[no-untyped-def]
    return MeResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        email_verified=user.email_verified,
        roles=user.roles,
        tenant_id=user.tenant_id,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    req: ChangePasswordRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> Response:
    await _build_service(db).change_password(
        user_id=user.id,
        current_password=req.current_password,
        new_password=req.new_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/staff", response_model=list[StaffMember])
async def list_staff(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[StaffMember]:
    users = await UserRepository(db).list_for_tenant(tenant_id=user.tenant_id)
    return [
        StaffMember(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            roles=list(u.roles),
            email_verified=u.email_verified,
        )
        for u in users
    ]


def _staff_to_schema(u) -> StaffMember:  # type: ignore[no-untyped-def]
    return StaffMember(
        id=u.id,
        email=u.email,
        first_name=u.first_name,
        last_name=u.last_name,
        roles=list(u.roles),
        email_verified=u.email_verified,
    )


@router.post(
    "/staff",
    response_model=StaffMember,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.STAFF_MANAGE))],
)
async def invite_staff(
    req: StaffInviteRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> StaffMember:
    invited = await _build_service(db).invite_staff(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        email=req.email,
        first_name=req.first_name,
        last_name=req.last_name,
        roles=req.roles,
    )
    return _staff_to_schema(invited)


@router.patch(
    "/staff/{user_id}/roles",
    response_model=StaffMember,
    dependencies=[Depends(requires(Permission.STAFF_MANAGE))],
)
async def update_staff_roles(
    user_id: str,
    req: StaffRolesUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> StaffMember:
    from uuid import UUID as _UUID

    updated = await _build_service(db).update_staff_roles(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        user_id=_UUID(user_id),
        roles=req.roles,
    )
    return _staff_to_schema(updated)


@router.delete(
    "/staff/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.STAFF_MANAGE))],
)
async def remove_staff(
    user_id: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> Response:
    from uuid import UUID as _UUID

    await _build_service(db).remove_staff(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        user_id=_UUID(user_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
