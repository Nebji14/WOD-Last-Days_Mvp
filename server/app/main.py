"""Point d'entrée du serveur : assemblage de l'application FastAPI.

Lancement en développement : ``uvicorn app.main:create_app --factory --reload``.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health
from app.api.deps import Container
from app.core.config import Settings, get_settings
from app.core.database import create_pool
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares
from app.core.rate_limit import RateLimiter
from app.core.security import SupabaseTokenVerifier
from app.gateways.supabase_auth import SupabaseAuthGateway
from app.repositories.accounts import PgAccountRepository
from app.services.auth import AuthService


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    """Construit l'application.

    Args:
        settings: configuration ; lue dans l'environnement si elle est omise.
        container: services déjà construits. Fourni par les tests pour
            remplacer la base et le fournisseur d'identité ; en exécution
            normale, les services réels sont créés au démarrage.
    """
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if container is not None:
            app.state.container = container
            yield
            return
        pool = await create_pool(settings)
        async with httpx.AsyncClient() as http_client:
            app.state.container = Container(
                settings=settings,
                auth_service=AuthService(
                    accounts=PgAccountRepository(pool),
                    identity=SupabaseAuthGateway(settings, http_client),
                    technical_email_domain=settings.technical_email_domain,
                ),
                token_verifier=SupabaseTokenVerifier(settings.supabase_url),
                rate_limiter=RateLimiter(),
            )
            try:
                yield
            finally:
                await pool.close()

    app = FastAPI(
        title="Hunter · Last Days",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )
    register_middlewares(app, settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    return app
