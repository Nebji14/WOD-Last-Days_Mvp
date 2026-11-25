"""Temps réel des fiches : siège mis à jour chez tous, fiche signalée à qui peut la lire."""

from collections.abc import Callable, Iterator
from contextlib import ExitStack
from typing import Any

import pytest
from starlette.testclient import WebSocketTestSession

from tests.api.helpers import Actor, game_master, player
from tests.api.test_characters import create, patch_sheet
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


def _event(session: WebSocketTestSession) -> tuple[str, dict[str, Any]]:
    event: dict[str, Any] = session.receive_json()
    return event["type"], event["data"]


def test_seat_shows_the_played_character_to_everyone(ctx: TestContext, connect: Connect) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    character = create(lea)

    ben_socket = connect(ben)
    _event(ben_socket)
    connect(lea)
    kind, state = _event(ben_socket)

    assert kind == "table.state"
    seats = {seat["display_name"]: seat["character"] for seat in state["seats"]}
    assert seats["ben.ard"] is None  # joueur sans personnage
    assert seats["lea.vale"] == {
        "id": character["id"],
        "name": "Isaac Thorne",
        "concept": "Chasseur de primes",
        "health_max": 7,
        "wound_track": "",
        "willpower_max": 4,
        "willpower_current": 4,
        "portrait": None,
    }


def test_sheet_change_updates_the_seat_for_all_and_the_sheet_for_owner_and_gm(
    ctx: TestContext, connect: Connect
) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    character = create(lea)
    sockets = {}
    for name, actor in (("gm", gm), ("lea", lea), ("ben", ben)):
        sockets[name] = connect(actor)
        for opened in sockets.values():
            _event(opened)

    patch_sheet(lea, character["sheets"][0]["id"], "willpower_current", 2, 4)

    # Le propriétaire et le MJ sont prévenus que la fiche a changé ; l'événement
    # ne porte que l'identifiant, jamais le contenu de la fiche.
    for name in ("gm", "lea"):
        assert _event(sockets[name]) == ("character.changed", {"character_id": character["id"]})
    # Tous, y compris un autre joueur, voient la jauge du siège.
    for name in ("gm", "lea", "ben"):
        kind, state = _event(sockets[name])
        assert kind == "table.state"
        assert state["seats"][0]["character"]["willpower_current"] == 2


def test_deleting_the_played_character_empties_the_seat(ctx: TestContext, connect: Connect) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    socket = connect(lea)
    _event(socket)

    lea.request("DELETE", f"/api/characters/{character_id}")

    assert _event(socket) == ("character.changed", {"character_id": character_id})
    kind, state = _event(socket)
    assert kind == "table.state"
    assert state["seats"][0]["character"] is None
