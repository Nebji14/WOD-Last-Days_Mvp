"""Gestion de son propre compte : noms, mot de passe, diffusion et droits."""

import pytest

from tests.api.helpers import GM_PASSWORD, Actor, error_code, game_master, player
from tests.conftest import PASSWORD, TestContext

NEW_PASSWORD = "nouvelle-traque-7"


def _password_body(current: str | None = PASSWORD, new: str = NEW_PASSWORD) -> dict[str, object]:
    return {"current_password": current, "password": new, "password_confirmation": new}


def _login_status(ctx: TestContext, username: str, password: str) -> int:
    response = ctx.client.post("/api/auth/login", json={"username": username, "password": password})
    ctx.client.cookies.clear()
    return int(response.status_code)


# --- Accès ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PATCH", "/api/account"),
        ("POST", "/api/account/password"),
        ("POST", "/api/account/google/link"),
        ("POST", "/api/account/google/confirm"),
        ("POST", "/api/account/google/unlink"),
    ],
)
def test_account_routes_require_a_session(ctx: TestContext, method: str, path: str) -> None:
    assert ctx.client.request(method, path, json={}).status_code == 401


# --- Noms -------------------------------------------------------------------------------


def test_player_changes_both_names(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request(
        "PATCH", "/api/account", json={"username": "lea2", "display_name": "  Léa  Vale "}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "lea2"
    assert response.json()["display_name"] == "Léa Vale"
    assert _login_status(ctx, "lea2", PASSWORD) == 200
    assert _login_status(ctx, "lea.vale", PASSWORD) == 401


def test_absent_field_keeps_its_value(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    lea.request("PATCH", "/api/account", json={"display_name": "Léa"})

    account = ctx.accounts.accounts[lea.account_id]
    assert (account.username, account.display_name) == ("lea.vale", "Léa")


def test_former_username_can_be_registered_again(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    lea.request("PATCH", "/api/account", json={"username": "lea2"})

    response = ctx.client.post(
        "/api/auth/register",
        json={"username": "lea.vale", "password": PASSWORD, "password_confirmation": PASSWORD},
    )

    assert response.status_code == 201


def test_taken_username_is_refused_ignoring_case(ctx: TestContext) -> None:
    player(ctx, "ben")
    lea = player(ctx, "lea.vale")

    response = lea.request("PATCH", "/api/account", json={"username": "BEN"})

    assert response.status_code == 409
    assert error_code(response) == "username_taken"


def test_own_username_can_change_case(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("PATCH", "/api/account", json={"username": "Lea.Vale"})

    assert response.json()["username"] == "Lea.Vale"


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"username": "é"}, "username_invalid"),
        ({"display_name": "   "}, "display_name_invalid"),
        ({"display_name": "x" * 41}, "display_name_invalid"),
        ({"role": "gm"}, "validation_error"),
    ],
)
def test_invalid_names_are_refused(ctx: TestContext, body: dict[str, str], code: str) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("PATCH", "/api/account", json=body)

    assert response.status_code == 422
    assert error_code(response) == code


def test_display_name_of_another_participant_is_refused(ctx: TestContext) -> None:
    game_master(ctx)
    lea = player(ctx, "lea.vale")

    response = lea.request("PATCH", "/api/account", json={"display_name": "Conteur"})

    assert response.status_code == 409
    assert error_code(response) == "display_name_taken"


def test_game_master_changes_names(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request("PATCH", "/api/account", json={"display_name": "Le Conteur"})

    assert response.json()["display_name"] == "Le Conteur"
    assert response.json()["role"] == "gm"


def test_new_display_name_reaches_the_table(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    with ctx.client.websocket_connect("/ws") as session:
        session.send_json({"type": "auth", "ticket": lea.ticket()})
        session.receive_json()

        lea.request("PATCH", "/api/account", json={"display_name": "Léa"})

        renamed, state = session.receive_json(), session.receive_json()

    assert renamed == {
        "type": "account.changed",
        "data": {"account_id": str(lea.account_id), "display_name": "Léa"},
    }
    assert state["type"] == "table.state"
    assert state["data"]["seats"][0]["display_name"] == "Léa"


# --- Mot de passe -----------------------------------------------------------------------


def test_new_password_replaces_the_former_one(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("POST", "/api/account/password", json=_password_body())

    assert response.status_code == 204
    assert _login_status(ctx, "lea.vale", NEW_PASSWORD) == 200
    assert _login_status(ctx, "lea.vale", PASSWORD) == 401


def test_changing_password_closes_other_sessions(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    other = ctx.client.post(
        "/api/auth/login", json={"username": "lea.vale", "password": PASSWORD}
    ).cookies["hunter_at"]
    ctx.client.cookies.clear()

    response = lea.request("POST", "/api/account/password", json=_password_body())
    renewed = response.cookies["hunter_at"]
    ctx.client.cookies.clear()

    assert Actor(ctx, lea.account_id, other).request("GET", "/api/auth/me").status_code == 401
    assert Actor(ctx, lea.account_id, renewed).request("GET", "/api/auth/me").status_code == 200


@pytest.mark.parametrize("current", [None, "", "mauvais-mdp-1"])
def test_wrong_current_password_changes_nothing(ctx: TestContext, current: str | None) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("POST", "/api/account/password", json=_password_body(current))

    assert response.status_code == 403
    assert error_code(response) == "wrong_password"
    assert _login_status(ctx, "lea.vale", PASSWORD) == 200


def test_weak_password_is_refused_with_its_rules(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("POST", "/api/account/password", json=_password_body(new="court"))

    assert error_code(response) == "password_too_weak"
    assert {"rule": "min_length"} in response.json()["error"]["details"]


def test_different_confirmation_is_refused(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    body = {**_password_body(), "password_confirmation": "autre-chose-1"}

    response = lea.request("POST", "/api/account/password", json=body)

    assert error_code(response) == "password_mismatch"


def test_current_password_attempts_are_limited(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    for _ in range(8):
        lea.request("POST", "/api/account/password", json=_password_body("mauvais-mdp-1"))

    response = lea.request("POST", "/api/account/password", json=_password_body())

    assert response.status_code == 429


def test_game_master_changes_password(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request("POST", "/api/account/password", json=_password_body(GM_PASSWORD))

    assert response.status_code == 204
