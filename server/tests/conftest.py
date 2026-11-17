"""Fixtures communes : application de test branchée sur des doublures."""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.deps import Container
from app.core.config import Settings
from app.core.rate_limit import RateLimiter
from app.main import create_app
from app.realtime.hub import ConnectionHub
from app.realtime.tickets import TicketStore
from app.services.auth import AuthService
from app.services.awakening import AwakeningService
from app.services.character_access import CharacterAccess
from app.services.characters import CharacterService
from app.services.chat import ChatService
from app.services.image_table import ImageTableService
from app.services.images import ImageService
from app.services.npcs import NpcService
from app.services.players import PlayerService
from app.services.sheet_items import SheetItemService
from app.services.table import TableService
from tests.fake_characters import FakeCharacterStore
from tests.fake_images import FakeFileStorage, FakeImageStore
from tests.fake_npcs import FakeNpcStore
from tests.fake_players import FakePlayerStore
from tests.fakes import (
    FakeAccountStore,
    FakeIdentityProvider,
    FakeMessageStore,
    FakeTokenVerifier,
)

ORIGIN = "http://localhost:3000"
PASSWORD = "chasseur-2026"


@dataclass
class TestContext:
    """Regroupe le client HTTP de test et les doublures qu'il utilise."""

    __test__ = False

    client: TestClient
    accounts: FakeAccountStore
    identity: FakeIdentityProvider
    auth_service: AuthService
    characters: FakeCharacterStore
    images: FakeImageStore
    storage: FakeFileStorage


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="development",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="publishable",
        supabase_secret_key=SecretStr("secret"),
        database_url=SecretStr("postgresql://unused"),
        allowed_origins=[ORIGIN],
        _env_file=None,
    )


@pytest.fixture
def ctx(settings: Settings) -> Iterator[TestContext]:
    accounts = FakeAccountStore()
    identity = FakeIdentityProvider()
    hub = ConnectionHub()
    characters = FakeCharacterStore(accounts)
    table_service = TableService(accounts, characters, hub)
    access = CharacterAccess(characters, accounts, hub, table_service.refresh)
    images = FakeImageStore()
    storage = FakeFileStorage()
    auth_service = AuthService(
        accounts, identity, settings.technical_email_domain, gm_access_path="mj-test"
    )
    container = Container(
        settings=settings,
        auth_service=auth_service,
        token_verifier=FakeTokenVerifier(identity),
        rate_limiter=RateLimiter(),
        chat_service=ChatService(FakeMessageStore(accounts), hub),
        table_service=table_service,
        hub=hub,
        tickets=TicketStore(),
        character_service=CharacterService(characters, characters, access),
        sheet_item_service=SheetItemService(characters, access),
        player_service=PlayerService(FakePlayerStore(accounts, characters), table_service),
        awakening_service=AwakeningService(characters, access),
        image_service=ImageService(images, storage, hub),
        image_table_service=ImageTableService(images, storage, hub),
        npc_service=NpcService(FakeNpcStore(characters), characters, access, hub),
    )
    with TestClient(create_app(settings, container), headers={"Origin": ORIGIN}) as client:
        yield TestContext(client, accounts, identity, auth_service, characters, images, storage)
