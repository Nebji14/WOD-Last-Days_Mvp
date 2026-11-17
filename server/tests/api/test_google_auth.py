"""Connexion avec Google : départ, retour, création du compte et contrôle de la page."""

import asyncio
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

from httpx import Response

from app.core.security import ACCESS_COOKIE
from app.gateways.supabase_auth import ExternalIdentity
from tests.conftest import PASSWORD, TestContext

GM_PASSWORD = "conteur-secret-9"


def _identity(name: str | None = "Léa Vale", email: str = "lea@gmail.com") -> ExternalIdentity:
    return ExternalIdentity(user_id=uuid4(), email=email, full_name=name)


def _google_login(
    ctx: TestContext, identity: ExternalIdentity, portal: str = "player", code: str = "code-1"
) -> Response:
    """Fait l'aller-retour complet : départ vers Google puis retour avec un code."""
    ctx.identity.google_codes[code] = identity
    start: Response = ctx.client.get(
        "/api/auth/google/start", params={"portal": portal}, follow_redirects=False
    )
    assert start.status_code == 303
    response: Response = ctx.client.get(
        "/api/auth/google/callback", params={"code": code}, follow_redirects=False
    )
    return response


def _query(response: Response) -> dict[str, list[str]]:
    return parse_qs(urlparse(response.headers["location"]).query)


# --- Départ -----------------------------------------------------------------------------


def test_start_redirects_to_provider_and_keeps_secret_in_cookie(ctx: TestContext) -> None:
    response = ctx.client.get("/api/auth/google/start", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("https://example.supabase.co/auth/v1/authorize")
    cookie = response.headers["set-cookie"]
    assert "hunter_oauth=player." in cookie
    assert "HttpOnly" in cookie


# --- Retour -----------------------------------------------------------------------------


def test_unknown_google_user_becomes_player_and_reaches_table(ctx: TestContext) -> None:
    identity = _identity()

    response = _google_login(ctx, identity)

    assert response.status_code == 303
    assert response.headers["location"] == "/table"
    assert ACCESS_COOKIE in response.cookies
    account = ctx.accounts.accounts[identity.user_id]
    assert account.username == "Lea.Vale"
    assert account.role.value == "player"


def test_returning_google_user_keeps_same_account(ctx: TestContext) -> None:
    identity = _identity()
    _google_login(ctx, identity)

    response = _google_login(ctx, identity, code="code-2")

    assert response.headers["location"] == "/table"
    assert len(ctx.accounts.accounts) == 1


def test_taken_username_gets_a_number(ctx: TestContext) -> None:
    _google_login(ctx, _identity())

    _google_login(ctx, _identity(email="autre@gmail.com"), code="code-2")

    usernames = sorted(account.username for account in ctx.accounts.accounts.values())
    assert usernames == ["Lea.Vale", "Lea.Vale2"]


def test_cancelled_google_login_returns_to_login_page(ctx: TestContext) -> None:
    ctx.client.get("/api/auth/google/start", follow_redirects=False)

    response = ctx.client.get(
        "/api/auth/google/callback", params={"error": "access_denied"}, follow_redirects=False
    )

    assert response.headers["location"] == "/connexion?erreur=google_failed"
    assert ACCESS_COOKIE not in response.cookies


def test_code_without_departure_cookie_is_refused(ctx: TestContext) -> None:
    identity = _identity()
    ctx.identity.google_codes["code-1"] = identity

    response = ctx.client.get(
        "/api/auth/google/callback", params={"code": "code-1"}, follow_redirects=False
    )

    assert _query(response) == {"erreur": ["google_failed"]}
    assert identity.user_id not in ctx.accounts.accounts


def test_disabled_account_cannot_sign_in_with_google(ctx: TestContext) -> None:
    identity = _identity()
    _google_login(ctx, identity)
    ctx.accounts.disable(identity.user_id)

    response = _google_login(ctx, identity, code="code-2")

    assert _query(response) == {"erreur": ["invalid_credentials"]}
    assert ACCESS_COOKIE not in response.cookies


# --- Page des joueurs ou page du MJ -----------------------------------------------------


def _create_gm(ctx: TestContext) -> UUID:
    gm = asyncio.run(ctx.auth_service.create_gm("conteur", "mj@example.org", GM_PASSWORD))
    return gm.id


def test_gm_google_account_on_player_page_is_sent_to_gm_page(ctx: TestContext) -> None:
    gm_identity = ExternalIdentity(user_id=_create_gm(ctx), email="mj@example.org", full_name="MJ")

    response = _google_login(ctx, gm_identity)

    assert response.headers["location"].startswith("/connexion?")
    assert _query(response) == {"erreur": ["wrong_portal_gm"], "acces": ["/mj-test"]}
    assert ACCESS_COOKIE not in response.cookies


def test_gm_signs_in_with_google_on_gm_page(ctx: TestContext) -> None:
    gm_identity = ExternalIdentity(user_id=_create_gm(ctx), email="mj@example.org", full_name="MJ")

    response = _google_login(ctx, gm_identity, portal="gm")

    assert response.headers["location"] == "/table"
    assert ACCESS_COOKIE in response.cookies


def test_gm_page_never_creates_an_account(ctx: TestContext) -> None:
    identity = _identity()

    response = _google_login(ctx, identity, portal="gm")

    assert response.headers["location"] == "/mj-test/connexion?erreur=wrong_portal_player"
    assert identity.user_id not in ctx.accounts.accounts


# --- Méthodes de connexion du profil ----------------------------------------------------


def test_login_methods_of_google_account(ctx: TestContext) -> None:
    _google_login(ctx, _identity())

    response = ctx.client.get("/api/auth/methods")

    assert response.json() == {"password": False, "google": True}


def test_login_methods_of_password_account(ctx: TestContext) -> None:
    ctx.client.post(
        "/api/auth/register",
        json={"username": "lea.vale", "password": PASSWORD, "password_confirmation": PASSWORD},
    )
    ctx.client.post("/api/auth/login", json={"username": "lea.vale", "password": PASSWORD})

    response = ctx.client.get("/api/auth/methods")

    assert response.json() == {"password": True, "google": False}
