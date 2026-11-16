"""Connexion temps réel : ticket, présence autour de la table, diffusion du chat."""

from collections.abc import Callable, Iterator
from contextlib import ExitStack
from typing import Any
from uuid import uuid4

import pytest
from starlette.testclient import WebSocketTestSession
from starlette.websockets import WebSocketDisconnect

from tests.api.helpers import Actor, game_master, player
from tests.conftest import TestContext

Connect = Callable[[Actor], WebSocketTestSession]


@pytest.fixture
def connect(ctx: TestContext) -> Iterator[Connect]:
    """Ouvre des connexions authentifiées, toutes refermées à la fin du test."""
    with ExitStack() as stack:

        def _open(actor: Actor) -> WebSocketTestSession:
            session = stack.enter_context(ctx.client.websocket_connect("/ws"))
            session.send_json({"type": "auth", "ticket": actor.ticket()})
            return session

        yield _open


def _next(session: WebSocketTestSession, event_type: str) -> dict[str, Any]:
    event: dict[str, Any] = session.receive_json()
    assert event["type"] == event_type
    data: dict[str, Any] = event["data"]
    return data


def _closing_code(session: WebSocketTestSession) -> int:
    with pytest.raises(WebSocketDisconnect) as closed:
        session.receive_json()
    return closed.value.code


# --- Ticket et authentification ---------------------------------------------------------


def test_ticket_requires_a_session(ctx: TestContext) -> None:
    assert ctx.client.post("/api/realtime/ticket").status_code == 401


def test_connection_from_unknown_origin_is_refused(ctx: TestContext) -> None:
    with (
        pytest.raises(WebSocketDisconnect),
        ctx.client.websocket_connect("/ws", headers={"Origin": "https://ailleurs.example"}),
    ):
        pass


@pytest.mark.parametrize(
    "first_message",
    ['{"type": "auth", "ticket": "inconnu"}', '{"type": "autre"}', "pas du json", "[]"],
)
def test_connection_without_valid_ticket_is_closed(ctx: TestContext, first_message: str) -> None:
    with ctx.client.websocket_connect("/ws") as session:
        session.send_text(first_message)

        assert _closing_code(session) == 4401


def test_ticket_is_single_use(ctx: TestContext, connect: Connect) -> None:
    lea = player(ctx, "lea.vale")
    ticket = lea.ticket()

    with ctx.client.websocket_connect("/ws") as first:
        first.send_json({"type": "auth", "ticket": ticket})
        _next(first, "table.state")
        with ctx.client.websocket_connect("/ws") as second:
            second.send_json({"type": "auth", "ticket": ticket})

            assert _closing_code(second) == 4401


# --- US-012 · CA2, US-028 · CA1 : présence ----------------------------------------------


def _summary(state: dict[str, Any]) -> list[tuple[int, str, bool]]:
    return [(s["position"], s["display_name"], s["online"]) for s in state["seats"]]


def test_arrivals_and_departures_are_broadcast(ctx: TestContext, connect: Connect) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")

    gm_socket = connect(gm)
    state = _next(gm_socket, "table.state")
    assert state == {"gm": {"display_name": "conteur", "online": True}, "seats": []}

    lea_socket = connect(lea)
    assert _next(lea_socket, "table.state") == _next(gm_socket, "table.state")

    connect(ben)
    assert _summary(_next(gm_socket, "table.state")) == [
        (0, "lea.vale", True),
        (1, "ben.ard", True),
    ]

    lea_socket.close()
    # 03-E2, Q03-7 : le siège reste affiché, hors ligne, à la même place.
    assert _summary(_next(gm_socket, "table.state")) == [
        (0, "lea.vale", False),
        (1, "ben.ard", True),
    ]

    lea_back = connect(lea)
    assert _next(lea_back, "table.state")["seats"][0] == {
        "position": 0,
        "account_id": str(lea.account_id),
        "display_name": "lea.vale",
        "online": True,
        "character": None,
    }


def test_gm_name_is_known_while_gm_is_offline(ctx: TestContext, connect: Connect) -> None:
    game_master(ctx)
    lea = player(ctx, "lea.vale")

    socket = connect(lea)

    assert _next(socket, "table.state")["gm"] == {"display_name": "conteur", "online": False}


def test_player_stays_online_while_one_window_remains(ctx: TestContext, connect: Connect) -> None:
    lea = player(ctx, "lea.vale")
    first = connect(lea)
    _next(first, "table.state")
    second = connect(lea)
    _next(first, "table.state")

    second.close()

    assert _next(first, "table.state")["seats"][0]["online"] is True


def test_tenth_player_finds_the_table_full(ctx: TestContext, connect: Connect) -> None:
    for index in range(9):
        _next(connect(player(ctx, f"joueur{index}")), "table.state")

    extra = connect(player(ctx, "joueur9"))

    assert _closing_code(extra) == 4409


# --- US-003, T3 : la déconnexion ferme le temps réel ------------------------------------


def test_logout_closes_the_realtime_connections_of_the_account(
    ctx: TestContext, connect: Connect
) -> None:
    lea = player(ctx, "lea.vale")
    socket = connect(lea)
    _next(socket, "table.state")

    lea.request("POST", "/api/auth/logout")

    assert _closing_code(socket) == 4401


# --- US-013 · CA3, US-030 · CA3 : diffusion du chat -------------------------------------


def test_chat_changes_are_broadcast_to_everyone(ctx: TestContext, connect: Connect) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    gm_socket = connect(gm)
    _next(gm_socket, "table.state")
    lea_socket = connect(lea)
    _next(lea_socket, "table.state")
    _next(gm_socket, "table.state")

    sent = lea.request(
        "POST", "/api/chat/messages", json={"client_token": str(uuid4()), "body": "Vous êtes là ?"}
    ).json()
    assert _next(gm_socket, "chat.message") == sent
    assert _next(lea_socket, "chat.message") == sent

    gm.request("PATCH", f"/api/chat/messages/{sent['id']}", json={"body": "Corrigé"})
    edited = _next(lea_socket, "chat.message")
    assert (edited["body"], edited["edited"]) == ("Corrigé", True)

    gm.request("DELETE", f"/api/chat/messages/{sent['id']}")
    deleted = _next(lea_socket, "chat.message")
    assert (deleted["body"], deleted["deleted_by"]) == (None, "gm")
