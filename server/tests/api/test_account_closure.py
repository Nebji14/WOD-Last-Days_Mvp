"""Départ d'un joueur : désactiver, supprimer définitivement, réactiver."""

from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import Response

from app.core.security import ACCESS_COOKIE
from app.gateways.supabase_auth import ExternalIdentity
from tests.api.helpers import GM_PASSWORD, Actor, error_code, game_master, player
from tests.api.test_characters import create
from tests.api.test_portraits import put_portrait
from tests.conftest import PASSWORD, TestContext

CLOSURES = ("disable", "delete")


def close(actor: Actor, action: str, **overrides: Any) -> Response:
    body = {"username": "lea.vale", "current_password": PASSWORD} | overrides
    response = actor.request("POST", f"/api/account/{action}", json=body)
    actor.ctx.client.cookies.clear()
    return response


def login_status(ctx: TestContext, username: str = "lea.vale") -> int:
    response = ctx.client.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    ctx.client.cookies.clear()
    return int(response.status_code)


def say(actor: Actor, body: str) -> dict[str, Any]:
    message: dict[str, Any] = actor.request(
        "POST", "/api/chat/messages", json={"client_token": str(uuid4()), "body": body}
    ).json()
    return message


def messages(actor: Actor) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = actor.request("GET", "/api/chat/messages").json()["messages"]
    return history


# --- Commun aux deux départs ------------------------------------------------------------


@pytest.mark.parametrize("action", CLOSURES)
def test_departure_closes_every_access(ctx: TestContext, action: str) -> None:
    lea = player(ctx, "lea.vale")

    response = close(lea, action)

    assert response.status_code == 204
    assert f'{ACCESS_COOKIE}=""' in response.headers["set-cookie"]
    assert lea.request("GET", "/api/auth/me").status_code == 401
    assert lea.request("POST", "/api/realtime/ticket").status_code == 401
    assert login_status(ctx) == 401


@pytest.mark.parametrize("action", CLOSURES)
def test_departure_is_announced_and_cannot_be_rewritten(ctx: TestContext, action: str) -> None:
    gm = game_master(ctx)
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")

    close(lea, action)

    notice = messages(ben)[-1]
    assert notice["body"].startswith("lea.vale a quitté")
    assert notice["notice"] == {"disable": "account_disabled", "delete": "account_deleted"}[action]
    path = f"/api/chat/messages/{notice['id']}"
    assert ben.request("DELETE", path).status_code == 403
    assert gm.request("PATCH", path, json={"body": "autre"}).status_code == 403
    assert gm.request("DELETE", path).status_code == 200


@pytest.mark.parametrize("action", CLOSURES)
@pytest.mark.parametrize("username", ["lea", "LEA.VALE", "lea.vale "])
def test_username_must_be_copied_exactly(ctx: TestContext, action: str, username: str) -> None:
    lea = player(ctx, "lea.vale")

    response = close(lea, action, username=username)

    assert error_code(response) == "confirmation_mismatch"
    assert login_status(ctx) == 200


@pytest.mark.parametrize("action", CLOSURES)
@pytest.mark.parametrize("password", [None, "", "mauvais-mdp-1"])
def test_password_is_required(ctx: TestContext, action: str, password: str | None) -> None:
    lea = player(ctx, "lea.vale")

    response = close(lea, action, current_password=password)

    assert error_code(response) == "wrong_password"
    assert login_status(ctx) == 200


@pytest.mark.parametrize("action", CLOSURES)
def test_gm_account_cannot_be_closed(ctx: TestContext, action: str) -> None:
    gm = game_master(ctx)

    response = close(gm, action, username="conteur", current_password=GM_PASSWORD)

    assert response.status_code == 403
    assert gm.request("GET", "/api/auth/me").status_code == 200


@pytest.mark.parametrize("action", CLOSURES)
def test_departure_requires_a_session(ctx: TestContext, action: str) -> None:
    assert ctx.client.post(f"/api/account/{action}", json={}).status_code == 401


@pytest.mark.parametrize("action", CLOSURES)
def test_google_account_needs_a_recent_login(ctx: TestContext, action: str) -> None:
    identity = ExternalIdentity(user_id=uuid4(), email="lea@gmail.com", full_name="Léa Vale")
    ctx.identity.google_codes["first"] = identity
    ctx.client.get("/api/auth/google/start", follow_redirects=False)
    token = ctx.client.get(
        "/api/auth/google/callback", params={"code": "first"}, follow_redirects=False
    ).cookies[ACCESS_COOKIE]
    ctx.client.cookies.clear()
    lea = Actor(ctx, identity.user_id, token)
    ctx.identity.authenticated_at[token] -= 3600
    body: dict[str, Any] = {"username": "Lea.Vale", "current_password": None}

    assert error_code(close(lea, action, **body)) == "reauthentication_required"

    ctx.identity.authenticated_at[token] += 3600
    assert close(lea, action, **body).status_code == 204


@pytest.mark.parametrize("action", CLOSURES)
def test_seat_is_freed_and_windows_are_closed(ctx: TestContext, action: str) -> None:
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    with (
        ctx.client.websocket_connect("/ws") as ben_socket,
        ctx.client.websocket_connect("/ws") as lea_socket,
    ):
        ben_socket.send_json({"type": "auth", "ticket": ben.ticket()})
        ben_socket.receive_json()
        lea_socket.send_json({"type": "auth", "ticket": lea.ticket()})
        assert len(ben_socket.receive_json()["data"]["seats"]) == 2

        close(lea, action)

        events = [ben_socket.receive_json()]
        while events[-1]["type"] != "table.state":
            events.append(ben_socket.receive_json())

    names = [seat["display_name"] for seat in events[-1]["data"]["seats"]]
    assert names == ["ben"]
    assert "chat.message" in [event["type"] for event in events]


# --- Désactiver et réactiver ------------------------------------------------------------


def test_disabled_account_keeps_its_data_until_the_gm_restores_it(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)
    say(lea, "À bientôt")

    close(lea, "disable")

    listed = gm.request("GET", "/api/players").json()["players"]
    assert [(p["username"], p["status"]) for p in listed] == [("lea.vale", "disabled")]
    assert gm.request("GET", f"/api/characters/{character['id']}").status_code == 200
    assert messages(gm)[0]["author"]["display_name"] == "lea.vale"

    path = f"/api/players/{lea.account_id}/reactivate"
    assert gm.request("POST", path).status_code == 204
    assert gm.request("POST", path).status_code == 404
    assert login_status(ctx) == 200


def test_reactivation_is_reserved_to_the_gm(ctx: TestContext) -> None:
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    close(lea, "disable")

    response = ben.request("POST", f"/api/players/{lea.account_id}/reactivate")

    assert response.status_code == 403
    assert login_status(ctx) == 401


# --- Supprimer définitivement -----------------------------------------------------------


def test_deletion_erases_everything_but_nameless_messages(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)
    put_portrait(lea, character["sheets"][0]["id"])
    say(lea, "Je pars")

    close(lea, "delete")

    assert lea.account_id not in ctx.accounts.accounts
    assert lea.account_id in ctx.identity.deleted
    assert ctx.storage.files == {}
    assert gm.request("GET", "/api/players").json()["players"] == []
    assert gm.request("GET", f"/api/characters/{character['id']}").status_code == 404
    kept = messages(gm)[0]
    assert kept["body"] == "Je pars"
    assert kept["author"] == {"id": None, "display_name": "", "role": "player"}


def test_deleted_username_can_be_taken_again(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    close(lea, "delete")

    newcomer = player(ctx, "lea.vale")

    assert newcomer.account_id != lea.account_id
    assert newcomer.request("GET", "/api/characters").json()["characters"] == []


def test_newcomer_has_no_right_on_nameless_messages(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    message = say(lea, "Je pars")
    close(lea, "delete")
    newcomer = player(ctx, "lea.vale")

    assert newcomer.request("DELETE", f"/api/chat/messages/{message['id']}").status_code == 403


def test_deleted_account_cannot_be_reactivated(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    close(lea, "delete")

    assert gm.request("POST", f"/api/players/{lea.account_id}/reactivate").status_code == 404
    assert gm.request("POST", f"/api/players/{UUID(int=0)}/reactivate").status_code == 404
