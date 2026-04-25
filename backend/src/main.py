"""FastAPI application entry."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import settings
from src.core.correlation import CorrelationIdMiddleware
from src.core.db import dispose_engine, engine_state
from src.core.errors import register_error_handlers
from src.core.idempotency import IdempotencyMiddleware
from src.core.logging import configure_logging
from src.core.real_ip import RealIpMiddleware
from src.modules.ai.router import router as ai_reports_router
from src.modules.ai.assistant_router import router as ai_assistant_router
from src.modules.ai.catalog_router import router as ai_catalog_router
from src.modules.ai.translate_router import router as ai_translate_router
from src.modules.ai.touch_router import router as campaign_touches_router
from src.modules.ai.procurement_vision_router import router as ai_procurement_vision_router
from src.modules.ai.inventory_vision_router import router as ai_inventory_vision_router
from src.modules.ai.age_vision_router import router as ai_age_vision_router
from src.modules.ai.jewelry_vision_router import router as ai_jewelry_vision_router
from src.modules.ai.planogram_router import router as ai_planogram_router
from src.modules.ai.cafeteria_vision_router import router as ai_cafeteria_vision_router
from src.modules.ai.supply_chain_router import router as ai_supply_chain_router
from src.modules.audit.router import router as audit_router
from src.modules.catalog.router import categories_router, router as catalog_router
from src.modules.customers.router import router as customers_router
from src.modules.discounts.router import router as discounts_router
from src.modules.identity.oauth_router import router as oauth_router
from src.modules.identity.router import router as identity_router
from src.modules.plugins.router import router as plugins_router
from src.modules.inventory.router import (
    locations_router,
    router as inventory_router,
)
from src.modules.procurement.router import (
    purchase_orders_router,
    suppliers_router,
)
from src.modules.procurement.product_suppliers_router import (
    router as product_suppliers_router,
)
from src.modules.reporting.router import router as reporting_router
from src.modules.sales.router import router as sales_router
from src.modules.shifts.router import router as shifts_router
from src.modules.tax.router import router as tax_router
from src.modules.tenants.router import router as tenant_router
from src.modules.media.router import router as media_router
from src.modules.personalization.router import router as personalization_router
from src.modules.personalization.recommendations_router import router as personalization_recs_router
from src.integrations.payments.webhooks import router as payment_webhooks_router
from src.verticals.deployment.self_checkout.router import router as self_checkout_router
from src.verticals.deployment.softpos.router import router as softpos_router
from src.verticals.fnb.bar_tabs.router import router as bar_tabs_router
from src.verticals.fnb.cafe_loyalty.router import router as cafe_loyalty_router
from src.verticals.fnb.cafeteria.router import router as cafeteria_router
from src.verticals.fnb.cloud_kitchen.router import router as cloud_kitchen_router
from src.verticals.fnb.food_truck.router import router as food_truck_router
from src.verticals.fnb.modifiers.router import router as modifiers_router
from src.verticals.fnb.preorders.router import router as preorders_router
from src.verticals.fnb.qsr.router import router as qsr_router
from src.verticals.fnb.restaurant.router import router as restaurant_router
from src.verticals.fnb.restaurant.ws import router as restaurant_ws_router
from src.verticals.hospitality.hotel.router import router as hotel_router
from src.verticals.hospitality.resort.router import router as resort_router
from src.verticals.logistics.deliveries.router import router as deliveries_router
from src.verticals.retail.age_restricted.router import router as age_restricted_router
from src.verticals.retail.apparel.router import router as apparel_router
from src.verticals.retail.bookstore.router import router as bookstore_router
from src.verticals.retail.cannabis.router import router as cannabis_router
from src.verticals.retail.consignment.router import router as consignment_router
from src.verticals.retail.departments.router import router as departments_router
from src.verticals.retail.electronics.router import router as electronics_router
from src.verticals.retail.florist.router import router as florist_router
from src.verticals.retail.furniture.router import router as furniture_router
from src.verticals.retail.grocery.router import router as grocery_router
from src.verticals.retail.hardware.router import router as hardware_router
from src.verticals.retail.pet_store.router import router as pet_store_router
from src.verticals.services.garage.router import router as garage_router
from src.verticals.services.gas_station.router import router as gas_station_router
from src.verticals.services.gym.router import router as gym_router
from src.verticals.services.laundry.router import router as laundry_router
from src.verticals.services.patient_records.router import router as patient_records_router
from src.verticals.services.rfid_memberships.router import router as rfid_memberships_router
from src.verticals.services.salon.router import router as salon_router
from src.verticals.specialty.cinema.router import router as cinema_router
from src.verticals.specialty.donations.router import router as donations_router
from src.verticals.specialty.jewelry.router import router as jewelry_router
from src.verticals.specialty.pharmacy.router import router as pharmacy_router
from src.verticals.specialty.popup.router import router as popup_router
from src.verticals.specialty.rental.router import router as rental_router
from src.verticals.specialty.tickets.router import router as tickets_router
from src.verticals.specialty.wholesale.router import router as wholesale_router


class StripSensitiveHeadersMiddleware(BaseHTTPMiddleware):
    """Remove framework/server headers that leak stack info."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        for header in ("Server", "X-Powered-By"):
            if header in response.headers:
                del response.headers[header]
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set baseline HTTP security headers for all responses.

    This is intentionally conservative for an API surface: no CSP here (belongs
    on the frontend) and no HSTS (should be set at the edge / proxy).
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    # Re-subscribe enabled plugins to the in-process event bus. Done inside
    # lifespan (not at import) so the DB engine + session factory are ready.
    try:
        from src.core.db import async_session_factory
        from src.modules.plugins.service import PluginService
        import structlog

        log = structlog.get_logger(__name__)
        async with async_session_factory() as session:
            count = await PluginService(session).bootstrap_all()
            log.info("plugins_bootstrapped", count=count)
    except Exception as exc:  # noqa: BLE001
        # A bad plugin shouldn't stop the API from booting. Log and move on.
        import structlog

        structlog.get_logger(__name__).warning(
            "plugins_bootstrap_failed", error=str(exc)
        )
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    is_prod = settings.app.env == "production"
    app = FastAPI(
        title="Bytloop POS API",
        version="0.0.1",
        debug=settings.app.debug and not is_prod,
        # In prod, disable public docs (see docs/PLAN.md §12 prod hardening)
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(RealIpMiddleware)
    if settings.app.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.app.allowed_hosts)
    app.add_middleware(StripSensitiveHeadersMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    # Idempotency runs close to the handler so it can see the final response;
    # correlation/session/CORS wrap around it.
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.app.secret_key.get_secret_value(),
        session_cookie="bytloop_oauth_session",
        same_site="lax",
        https_only=settings.app.env == "production",
        max_age=600,  # 10 min — only holds OAuth state while user consents
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-Id"],
    )

    register_error_handlers(app)

    app.include_router(identity_router)
    app.include_router(oauth_router)
    app.include_router(catalog_router)
    app.include_router(categories_router)
    app.include_router(inventory_router)
    app.include_router(locations_router)
    app.include_router(suppliers_router)
    app.include_router(purchase_orders_router)
    app.include_router(product_suppliers_router)
    app.include_router(customers_router)
    app.include_router(discounts_router)
    app.include_router(tax_router)
    app.include_router(tenant_router)
    app.include_router(media_router)
    app.include_router(personalization_router)
    app.include_router(personalization_recs_router)
    app.include_router(shifts_router)
    app.include_router(sales_router)
    app.include_router(reporting_router)
    app.include_router(ai_reports_router)
    app.include_router(ai_assistant_router)
    app.include_router(ai_catalog_router)
    app.include_router(ai_translate_router)
    app.include_router(ai_procurement_vision_router)
    app.include_router(ai_inventory_vision_router)
    app.include_router(ai_age_vision_router)
    app.include_router(ai_jewelry_vision_router)
    app.include_router(ai_planogram_router)
    app.include_router(ai_cafeteria_vision_router)
    app.include_router(ai_supply_chain_router)
    app.include_router(campaign_touches_router)
    app.include_router(audit_router)
    app.include_router(plugins_router)
    app.include_router(payment_webhooks_router)
    app.include_router(restaurant_router)
    app.include_router(restaurant_ws_router)
    app.include_router(apparel_router)
    app.include_router(grocery_router)
    app.include_router(pharmacy_router)
    app.include_router(garage_router)
    app.include_router(gym_router)
    app.include_router(salon_router)
    app.include_router(hotel_router)
    app.include_router(cinema_router)
    app.include_router(rental_router)
    app.include_router(jewelry_router)
    # 35-variant expansion (verticals shipped in batch via parallel agents)
    app.include_router(electronics_router)
    app.include_router(age_restricted_router)
    app.include_router(consignment_router)
    app.include_router(cannabis_router)
    app.include_router(modifiers_router)
    app.include_router(preorders_router)
    app.include_router(bar_tabs_router)
    app.include_router(deliveries_router)
    app.include_router(rfid_memberships_router)
    app.include_router(gas_station_router)
    app.include_router(laundry_router)
    app.include_router(patient_records_router)
    app.include_router(tickets_router)
    app.include_router(donations_router)
    app.include_router(wholesale_router)
    # Profile-only → dedicated: the last 15 variants to reach full-module parity.
    app.include_router(furniture_router)
    app.include_router(bookstore_router)
    app.include_router(florist_router)
    app.include_router(pet_store_router)
    app.include_router(hardware_router)
    app.include_router(departments_router)
    app.include_router(cafe_loyalty_router)
    app.include_router(qsr_router)
    app.include_router(cloud_kitchen_router)
    app.include_router(cafeteria_router)
    app.include_router(food_truck_router)
    app.include_router(resort_router)
    app.include_router(popup_router)
    app.include_router(self_checkout_router)
    app.include_router(softpos_router)

    @app.get("/health/live", tags=["ops"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["ops"])
    async def ready() -> dict[str, object]:
        # Kept intentionally light — Redis/DB checks go through circuit breakers
        # and should never take this endpoint offline.
        return {"status": "ok", "db_pool": engine_state()}

    @app.get("/config", tags=["ops"])
    async def public_config() -> dict[str, object]:
        """Client-safe subset of Global Config (see docs/PLAN.md §4a)."""
        return {
            "currencies": {
                "supported": settings.currency.supported,
                "default": settings.currency.default,
            },
            "payments": {
                "bdProviders": settings.payments.bd_providers,
                "globalProviders": settings.payments.global_providers,
            },
            "auth": {
                "resendCooldownSeconds": settings.auth.resend_cooldown_seconds,
                "passwordMinLength": settings.auth.password_min_length,
            },
        }

    return app


app = create_app()
