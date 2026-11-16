"""Routes d'authentification : US-001, US-002, US-003, US-023 et droits d'accès."""

import asyncio

import pytest
from httpx import Response

from app.core.errors import AppError
from app.core.security import ACCESS_COOKIE, REFRESH_COOKIE
from tests.conftest import ORIGIN, PASSWORD, TestContext

GM_PASSWORD = "conteur-secret-9"


def _register(ctx: TestContext, username: str = "lea.vale", password: str = PASSWORD) -> Response:
    response: Response = ctx.client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "password_confirmation": password},
    )
    return response


def _login(
    ctx: TestContext, username: str = "lea.vale", password: str = PASSWORD, gm: bool = False
) -> Response:
    path = "/api/auth/gm/login" if gm else "/api/auth/login"
    response: Response = ctx.client.post(path, json={"username": username, "password": password})
    return response


def _create_gm(ctx: TestContext) -> None:
    asyncio.run(ctx.auth_service.create_gm("conteur", "mj@example.org", GM_PASSWORD))


def _error_code(response: Response) -> str:
    return str(response.json()["error"]["code"])


# --- US-001 : inscription (02b) ---------------------------------------------------------


def test_register_creates_player_without_opening_session(ctx: TestContext) -> None:
    response = _register(ctx)

    assert response.status_code == 201
    assert response.json()["role"] == "player"
    assert response.json()["display_name"] == "lea.vale"
    assert "auth_email" not in response.json()
    assert ACCESS_COOKIE not in response.cookies  # 02b-C3 : pas de connexion automatique


def test_register_rejects_taken_username_ignoring_case(ctx: TestContext) -> None:
    _register(ctx)

    response = _register(ctx, username="LEA.VALE")

    assert response.status_code == 409
    assert _error_code(response) == "username_taken"


def test_register_rejects_password_mismatch(ctx: TestContext) -> None:
    response = ctx.client.post(
        "/api/auth/register",
        json={"username": "lea", "password": PASSWORD, "password_confirmation": PASSWORD + "x"},
    )

    assert _error_code(response) == "password_mismatch"


def test_register_rejects_weak_password_and_lists_rules(ctx: TestContext) -> None:
    response = _register(ctx, password="court")

    assert _error_code(response) == "password_too_weak"
    rules = {item["rule"] for item in response.json()["error"]["details"]}
    assert {"min_length", "digit"} <= rules


def test_register_rejects_invalid_username(ctx: TestContext) -> None:
    assert _error_code(_register(ctx, username="léa vale")) == "username_invalid"


def test_validation_error_never_echoes_input(ctx: TestContext) -> None:
    response = ctx.client.post(
        "/api/auth/register", json={"username": "lea", "password": "secret-value-1"}
    )

    assert response.status_code == 422
    assert "secret-value-1" not in response.text


# --- US-002 : connexion joueur (02a) ----------------------------------------------------


def test_login_sets_http_only_session_cookies(ctx: TestContext) -> None:
    _register(ctx)

    response = _login(ctx, username="Lea.Vale")

    assert response.status_code == 200
    assert response.json()["username"] == "lea.vale"
    set_cookie = response.headers.get_list("set-cookie")
    assert len(set_cookie) == 2
    assert all("HttpOnly" in cookie and "SameSite=lax" in cookie for cookie in set_cookie)
    assert "access-" not in response.text


def test_login_errors_are_identical_for_unknown_user_and_wrong_password(ctx: TestContext) -> None:
    _register(ctx)

    wrong_password = _login(ctx, password="mauvais-mot-2")
    unknown_user = _login(ctx, username="inconnu")

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["error"]["message"] == unknown_user.json()["error"]["message"]
    assert _error_code(wrong_password) == _error_code(unknown_user) == "invalid_credentials"


def test_disabled_account_cannot_login_or_keep_session(ctx: TestContext) -> None:
    account_id = _register(ctx).json()["id"]
    _login(ctx)
    ctx.accounts.disable(
        next(a.id for a in ctx.accounts.accounts.values() if str(a.id) == account_id)
    )

    assert ctx.client.get("/api/auth/me").status_code == 401
    assert _error_code(_login(ctx)) == "invalid_credentials"


# --- 02a-E6 / 02c-E6 : mauvais accès ----------------------------------------------------


def test_gm_on_player_portal_is_refused_without_session(ctx: TestContext) -> None:
    _create_gm(ctx)

    response = _login(ctx, username="conteur", password=GM_PASSWORD)

    assert response.status_code == 403
    assert _error_code(response) == "wrong_portal_gm"
    assert ACCESS_COOKIE not in response.cookies
    assert ctx.identity.sessions == {}


def test_gm_with_wrong_password_on_player_portal_gets_generic_error(ctx: TestContext) -> None:
    _create_gm(ctx)

    assert (
        _error_code(_login(ctx, username="conteur", password="mauvais-mot-2"))
        == "invalid_credentials"
    )


def test_player_on_gm_portal_is_refused_without_session(ctx: TestContext) -> None:
    _register(ctx)

    response = _login(ctx, gm=True)

    assert response.status_code == 403
    assert _error_code(response) == "wrong_portal_player"
    assert ctx.identity.sessions == {}


# --- US-023 : connexion du MJ (02c) -----------------------------------------------------


def test_gm_login_on_gm_portal(ctx: TestContext) -> None:
    _create_gm(ctx)

    response = _login(ctx, username="conteur", password=GM_PASSWORD, gm=True)

    assert response.status_code == 200
    assert response.json()["role"] == "gm"


def test_only_one_gm_account_can_exist(ctx: TestContext) -> None:
    _create_gm(ctx)

    with pytest.raises(AppError) as raised:
        asyncio.run(ctx.auth_service.create_gm("second", "autre@example.org", GM_PASSWORD))

    assert raised.value.code == "username_taken"
    assert len(ctx.identity.deleted) == 1  # l'identité orpheline est supprimée


# --- Session : /me, rafraîchissement, US-003 déconnexion --------------------------------


def test_me_requires_a_session(ctx: TestContext) -> None:
    response = ctx.client.get("/api/auth/me")

    assert response.status_code == 401
    assert _error_code(response) == "not_authenticated"


def test_me_rejects_a_forged_token(ctx: TestContext) -> None:
    ctx.client.cookies.set(ACCESS_COOKIE, "jeton-forge")

    assert ctx.client.get("/api/auth/me").status_code == 401


def test_me_returns_current_account(ctx: TestContext) -> None:
    _register(ctx)
    _login(ctx)

    response = ctx.client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "lea.vale"


def test_refresh_rotates_session(ctx: TestContext) -> None:
    _register(ctx)
    _login(ctx)
    first_access = ctx.client.cookies.get(ACCESS_COOKIE)

    response = ctx.client.post("/api/auth/refresh")

    assert response.status_code == 204
    assert ctx.client.cookies.get(ACCESS_COOKIE) != first_access
    assert ctx.client.get("/api/auth/me").status_code == 200


def test_refresh_without_cookie_is_refused(ctx: TestContext) -> None:
    assert ctx.client.post("/api/auth/refresh").status_code == 401


def test_logout_revokes_session_and_clears_cookies(ctx: TestContext) -> None:
    _register(ctx)
    _login(ctx)
    access = ctx.client.cookies.get(ACCESS_COOKIE)

    response = ctx.client.post("/api/auth/logout")

    assert response.status_code == 204
    assert ctx.client.cookies.get(ACCESS_COOKIE) is None
    assert ctx.client.cookies.get(REFRESH_COOKIE) is None
    assert access not in ctx.identity.sessions


# --- Protections transverses ------------------------------------------------------------


def test_unknown_origin_is_refused_on_mutating_request(ctx: TestContext) -> None:
    response = ctx.client.post(
        "/api/auth/login",
        json={"username": "lea", "password": PASSWORD},
        headers={"Origin": "https://attaquant.example"},
    )

    assert response.status_code == 403
    assert _error_code(response) == "forbidden_origin"


def test_login_is_rate_limited_per_username(ctx: TestContext) -> None:
    _register(ctx)

    statuses = [_login(ctx, password="mauvais-mot-2").status_code for _ in range(9)]

    assert statuses[:8] == [401] * 8
    assert statuses[8] == 429


def test_responses_carry_security_headers_and_request_id(ctx: TestContext) -> None:
    response = ctx.client.get("/api/health", headers={"Origin": ORIGIN})

    assert response.json() == {"status": "ok"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Request-ID"]
