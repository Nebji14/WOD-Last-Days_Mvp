"""Point d'entrée du serveur : assemblage de l'application FastAPI.

Lancement en développement : ``uvicorn app.main:create_app --factory --reload``.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    characters,
    chat,
    dice,
    google_auth,
    health,
    images,
    npcs,
    players,
    realtime,
    sheet_items,
)
from app.api.deps import Container
from app.api.google_auth import google_callback_url
from app.core.config import Settings, get_settings
from app.core.database import create_pool
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middlewares
from app.core.rate_limit import RateLimiter
from app.core.security import SupabaseTokenVerifier
from app.gateways.supabase_auth import SupabaseAuthGateway
from app.gateways.supabase_storage import SupabaseStorageGateway
from app.realtime import endpoint as realtime_endpoint
from app.realtime.hub import ConnectionHub
from app.realtime.tickets import TicketStore
from app.repositories.accounts import PgAccountRepository
from app.repositories.characters import PgCharacterRepository
from app.repositories.chat import PgChatRepository
from app.repositories.images import PgImageRepository
from app.repositories.npcs import PgNpcRepository
from app.repositories.players import PgPlayerRepository
from app.repositories.sheet_items import PgSheetItemRepository
from app.services.auth import AuthService
from app.services.awakening import AwakeningService
from app.services.character_access import CharacterAccess
from app.services.characters import CharacterService
from app.services.chat import ChatService
from app.services.dice import DiceService
from app.services.google_auth import GoogleAuthService
from app.services.image_table import ImageTableService
from app.services.images import ImageService
from app.services.npcs import NpcService
from app.services.players import PlayerService
from app.services.sheet_items import SheetItemService
from app.services.table import TableService

# Relance de secours, si le lanceur a quitté la table : son écran relance de
# lui-même quelques secondes après avoir montré les dés, même si d'autres jets
# passent avant le sien.
_AUTO_REROLL_SECONDS = 60.0


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
        accounts = PgAccountRepository(pool)
        hub = ConnectionHub()
        character_repository = PgCharacterRepository(pool)
        item_repository = PgSheetItemRepository(pool)
        table_service = TableService(accounts, character_repository, hub)
        access = CharacterAccess(character_repository, accounts, hub, table_service.refresh)
        image_repository = PgImageRepository(pool)
        async with httpx.AsyncClient() as http_client:
            storage = SupabaseStorageGateway(settings, http_client)
            identity = SupabaseAuthGateway(settings, http_client)
            chat_service = ChatService(PgChatRepository(pool), hub)
            app.state.container = Container(
                settings=settings,
                auth_service=AuthService(
                    accounts=accounts,
                    identity=identity,
                    technical_email_domain=settings.technical_email_domain,
                    gm_access_path=settings.gm_access_path,
                ),
                google_auth_service=GoogleAuthService(
                    accounts=accounts,
                    identity=identity,
                    redirect_url=google_callback_url(settings),
                    gm_access_path=settings.gm_access_path,
                ),
                token_verifier=SupabaseTokenVerifier(settings.supabase_url),
                rate_limiter=RateLimiter(),
                chat_service=chat_service,
                table_service=table_service,
                hub=hub,
                tickets=TicketStore(),
                character_service=CharacterService(character_repository, item_repository, access),
                sheet_item_service=SheetItemService(item_repository, access),
                player_service=PlayerService(PgPlayerRepository(pool), table_service),
                awakening_service=AwakeningService(character_repository, access),
                image_service=ImageService(image_repository, storage, hub),
                image_table_service=ImageTableService(image_repository, storage, hub),
                npc_service=NpcService(PgNpcRepository(pool), character_repository, access, hub),
                dice_service=DiceService(
                    access,
                    character_repository,
                    hub,
                    chat_service,
                    auto_reroll_seconds=_AUTO_REROLL_SECONDS,
                ),
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
    app.include_router(google_auth.router)
    app.include_router(chat.router)
    app.include_router(dice.router)
    app.include_router(characters.router)
    app.include_router(sheet_items.router)
    app.include_router(players.router)
    app.include_router(images.router)
    app.include_router(npcs.router)
    app.include_router(realtime.router)
    app.include_router(realtime_endpoint.router)
    return app
