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
from app.services.auth import AuthService
from tests.fakes import FakeAccountStore, FakeIdentityProvider, FakeTokenVerifier

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
    auth_service = AuthService(
        accounts, identity, settings.technical_email_domain, gm_access_path="mj-test"
    )
    container = Container(
        settings=settings,
        auth_service=auth_service,
        token_verifier=FakeTokenVerifier(identity),
        rate_limiter=RateLimiter(),
    )
    with TestClient(create_app(settings, container), headers={"Origin": ORIGIN}) as client:
        yield TestContext(client, accounts, identity, auth_service)
