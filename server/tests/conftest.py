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
from app.services.account import AccountService
from app.services.auth import AuthService
from app.services.awakening import AwakeningService
from app.services.character_access import CharacterAccess
from app.services.characters import CharacterService
from app.services.chat import ChatService
from app.services.dice import DiceService
from app.services.google_auth import GoogleAuthService
from app.services.google_link import GoogleLinkService
from app.services.image_table import ImageTableService
from app.services.images import ImageService
from app.services.npcs import NpcService
from app.services.owner_check import OwnerCheck
from app.services.players import PlayerService
from app.services.resources import ResourceService
from app.services.roll_costs import RollCosts
from app.services.sheet_items import SheetItemService
from app.services.table import TableService
from tests.fake_characters import FakeCharacterStore
from tests.fake_dice import ScriptedDice
from tests.fake_images import FakeFileStorage, FakeImageStore
from tests.fake_npcs import FakeNpcStore
from tests.fake_players import FakePlayerStore
from tests.fake_resources import FakeResourceStore
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
    dice: ScriptedDice


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="development",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="publishable",
        supabase_secret_key=SecretStr("secret"),
        database_url=SecretStr("postgresql://unused"),
        allowed_origins=[ORIGIN],
        gm_access_path="mj-test",
        _env_file=None,
    )


@pytest.fixture
def ctx(settings: Settings) -> Iterator[TestContext]:
    accounts = FakeAccountStore()
    identity = FakeIdentityProvider()
    accounts.identity = identity
    owner_check = OwnerCheck(accounts, identity)
    hub = ConnectionHub()
    characters = FakeCharacterStore(accounts)
    resources = FakeResourceStore(characters)
    table_service = TableService(accounts, characters, hub)
    access = CharacterAccess(characters, accounts, hub, table_service.refresh)
    images = FakeImageStore()
    storage = FakeFileStorage()
    auth_service = AuthService(
        accounts, identity, settings.technical_email_domain, gm_access_path="mj-test"
    )
    chat_service = ChatService(FakeMessageStore(accounts), hub)
    dice = ScriptedDice()
    container = Container(
        settings=settings,
        auth_service=auth_service,
        account_service=AccountService(accounts, identity, owner_check, table_service, hub),
        google_auth_service=GoogleAuthService(
            accounts, identity, f"{ORIGIN}/api/auth/google/callback", gm_access_path="mj-test"
        ),
        google_link_service=GoogleLinkService(
            accounts, identity, owner_check, f"{ORIGIN}/api/auth/google/callback"
        ),
        token_verifier=FakeTokenVerifier(identity),
        rate_limiter=RateLimiter(),
        chat_service=chat_service,
        table_service=table_service,
        hub=hub,
        tickets=TicketStore(),
        character_service=CharacterService(characters, characters, access),
        sheet_item_service=SheetItemService(characters, access),
        resource_service=ResourceService(resources, access),
        player_service=PlayerService(FakePlayerStore(accounts, characters), table_service),
        awakening_service=AwakeningService(characters, access),
        image_service=ImageService(images, storage, hub),
        image_table_service=ImageTableService(images, storage, hub),
        npc_service=NpcService(FakeNpcStore(characters), characters, access, hub),
        dice_service=DiceService(
            access,
            RollCosts(access, characters, resources),
            hub,
            chat_service,
            roll_die=dice.roll,
        ),
    )
    with TestClient(create_app(settings, container), headers={"Origin": ORIGIN}) as client:
        yield TestContext(
            client, accounts, identity, auth_service, characters, images, storage, dice
        )
