"""Connexion Google d'un compte ouvert : rattacher, remplacer, retirer, confirmer."""

from uuid import UUID, uuid4

import pytest
from httpx import Response

from app.core.security import ACCESS_COOKIE
from app.gateways.supabase_auth import ExternalIdentity
from app.services.google_flow import GoogleFlow
from tests.api.helpers import Actor, error_code, player
from tests.conftest import PASSWORD, TestContext

NEW_PASSWORD = "nouvelle-traque-7"


def _google_player(ctx: TestContext) -> Actor:
    """Crée un compte par sa première connexion Google."""
    identity = ExternalIdentity(user_id=uuid4(), email="lea@gmail.com", full_name="Léa Vale")
    ctx.identity.google_codes["first"] = identity
    ctx.client.get("/api/auth/google/start", follow_redirects=False)
    response = ctx.client.get(
        "/api/auth/google/callback", params={"code": "first"}, follow_redirects=False
    )
    token = response.cookies[ACCESS_COOKIE]
    ctx.client.cookies.clear()
    return Actor(ctx, identity.user_id, token)


def _expire_recent_login(ctx: TestContext, actor: Actor) -> None:
    ctx.identity.authenticated_at[actor.token] -= 3600


def _return_from_google(
    ctx: TestContext, start: Response, user_id: UUID, **params: str
) -> Response:
    """Retour de Google avec le cookie posé au départ."""
    known = ctx.accounts.accounts.get(user_id)
    email = known.auth_email if known is not None else "inconnu@gmail.com"
    ctx.identity.google_codes["code"] = ExternalIdentity(
        user_id=user_id, email=email, full_name=None
    )
    flow = start.cookies["hunter_oauth"]
    ctx.client.cookies.clear()
    response: Response = ctx.client.get(
        "/api/auth/google/callback",
        params=params or {"code": "code"},
        headers={"Cookie": f"hunter_oauth={flow}"},
        follow_redirects=False,
    )
    ctx.client.cookies.clear()
    return response


# --- Rattacher et remplacer -------------------------------------------------------------


def test_password_account_links_google(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    start = lea.request("POST", "/api/account/google/link", json={"current_password": PASSWORD})
    response = _return_from_google(ctx, start, lea.account_id)

    assert start.json()["url"].startswith("https://example.supabase.co/")
    assert response.headers["location"] == "/profil?google=linked"
    methods = lea.request("GET", "/api/auth/methods").json()
    assert methods == {"password": True, "google": True}


def test_linking_again_replaces_the_former_google_account(ctx: TestContext) -> None:
    lea = _google_player(ctx)
    former = ctx.identity.google_links[lea.account_id][0].identity_id

    start = lea.request("POST", "/api/account/google/link", json={})
    _return_from_google(ctx, start, lea.account_id)

    remaining = [link.identity_id for link in ctx.identity.google_links[lea.account_id]]
    assert len(remaining) == 1
    assert former not in remaining


def test_linking_requires_the_current_password(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("POST", "/api/account/google/link", json={"current_password": "faux"})

    assert response.status_code == 403
    assert error_code(response) == "wrong_password"
    assert "hunter_oauth" not in response.cookies


def test_google_account_of_someone_else_is_reported(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    start = lea.request("POST", "/api/account/google/link", json={"current_password": PASSWORD})

    response = _return_from_google(ctx, start, lea.account_id, error_code="identity_already_exists")

    assert response.headers["location"] == "/profil?google=google_already_linked"


def test_cancelled_link_returns_to_profile(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    start = lea.request("POST", "/api/account/google/link", json={"current_password": PASSWORD})

    response = _return_from_google(ctx, start, lea.account_id, error="access_denied")

    assert response.headers["location"] == "/profil?google=google_failed"


# --- Confirmer le titulaire -------------------------------------------------------------


def test_google_only_account_sets_a_first_password(ctx: TestContext) -> None:
    lea = _google_player(ctx)

    response = lea.request(
        "POST",
        "/api/account/password",
        json={"password": NEW_PASSWORD, "password_confirmation": NEW_PASSWORD},
    )

    assert response.status_code == 204
    ctx.client.cookies.clear()
    login = ctx.client.post(
        "/api/auth/login", json={"username": "Lea.Vale", "password": NEW_PASSWORD}
    )
    assert login.status_code == 200


def test_google_only_account_with_an_old_login_must_confirm(ctx: TestContext) -> None:
    lea = _google_player(ctx)
    _expire_recent_login(ctx, lea)

    response = lea.request(
        "POST",
        "/api/account/password",
        json={"password": NEW_PASSWORD, "password_confirmation": NEW_PASSWORD},
    )

    assert response.status_code == 403
    assert error_code(response) == "reauthentication_required"


def test_confirmation_opens_a_recent_session(ctx: TestContext) -> None:
    lea = _google_player(ctx)
    _expire_recent_login(ctx, lea)

    start = lea.request("POST", "/api/account/google/confirm")
    response = _return_from_google(ctx, start, lea.account_id)

    assert response.headers["location"] == "/profil?google=confirmed"
    assert ACCESS_COOKIE in response.cookies


def test_confirmation_with_another_google_account_is_refused(ctx: TestContext) -> None:
    lea = _google_player(ctx)
    stranger = uuid4()

    start = lea.request("POST", "/api/account/google/confirm")
    response = _return_from_google(ctx, start, stranger)

    assert response.headers["location"] == "/profil?google=google_failed"
    assert ACCESS_COOKIE not in response.cookies
    assert stranger in ctx.identity.deleted
    assert stranger not in ctx.accounts.accounts


def test_confirmation_never_deletes_a_known_account(ctx: TestContext) -> None:
    lea = _google_player(ctx)
    ben = player(ctx, "ben")

    start = lea.request("POST", "/api/account/google/confirm")
    response = _return_from_google(ctx, start, ben.account_id)

    assert response.headers["location"] == "/profil?google=google_failed"
    assert ctx.identity.deleted == []


# --- Retirer ----------------------------------------------------------------------------


def test_google_is_removed_when_a_password_remains(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    start = lea.request("POST", "/api/account/google/link", json={"current_password": PASSWORD})
    _return_from_google(ctx, start, lea.account_id)

    response = lea.request(
        "POST", "/api/account/google/unlink", json={"current_password": PASSWORD}
    )

    assert response.status_code == 204
    methods = lea.request("GET", "/api/auth/methods").json()
    assert methods == {"password": True, "google": False}


def test_last_login_method_cannot_be_removed(ctx: TestContext) -> None:
    lea = _google_player(ctx)

    response = lea.request("POST", "/api/account/google/unlink", json={})

    assert response.status_code == 409
    assert error_code(response) == "last_login_method"


# --- Cookie du départ -------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [None, "", "player", "player.link..secret", "player.autre..secret", "x.login..secret"],
)
def test_altered_departure_cookie_is_refused(value: str | None) -> None:
    assert GoogleFlow.decode(value) is None
