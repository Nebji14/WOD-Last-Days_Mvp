"""Routes du chat général : US-013, US-029, US-030 et droits d'accès."""

from uuid import uuid4

from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.conftest import TestContext


def _send(actor: Actor, body: str = "Bonsoir à tous.", token: str | None = None) -> Response:
    return actor.request(
        "POST", "/api/chat/messages", json={"client_token": token or str(uuid4()), "body": body}
    )


def _history(actor: Actor, query: str = "") -> Response:
    return actor.request("GET", f"/api/chat/messages{query}")


# --- Accès ------------------------------------------------------------------------------


def test_chat_requires_a_session(ctx: TestContext) -> None:
    assert ctx.client.get("/api/chat/messages").status_code == 401
    refused = ctx.client.post(
        "/api/chat/messages", json={"client_token": str(uuid4()), "body": "x"}
    )
    assert refused.status_code == 401


# --- US-013 · CA5, US-029 : envoi -------------------------------------------------------


def test_player_sends_a_message(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = _send(lea, "  Qui a vu la lumière ?  ")

    assert response.status_code == 201
    message = response.json()
    assert message["body"] == "Qui a vu la lumière ?"
    assert message["author"] == {
        "id": str(lea.account_id),
        "display_name": "lea.vale",
        "role": "player",
    }
    assert message["edited"] is False
    assert message["deleted_by"] is None


def test_gm_message_carries_the_gm_role(ctx: TestContext) -> None:
    gm = game_master(ctx)

    assert _send(gm).json()["author"]["role"] == "gm"


def test_empty_or_oversized_message_is_rejected(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    assert error_code(_send(lea, "   ")) == "validation_error"
    assert error_code(_send(lea, "x" * 2001)) == "validation_error"
    assert _send(lea, "x" * 2000).status_code == 201


def test_resending_with_the_same_token_creates_no_duplicate(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    token = str(uuid4())

    first = _send(lea, "Envoi rejoué", token)
    second = _send(lea, "Envoi rejoué", token)

    assert first.json()["id"] == second.json()["id"]
    assert len(_history(lea).json()["messages"]) == 1


def test_sending_is_rate_limited_per_account(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    statuses = [_send(lea).status_code for _ in range(11)]

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429


# --- US-013 · CA1, CA2 : historique -----------------------------------------------------


def test_history_returns_latest_messages_in_chronological_order(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    for index in range(3):
        _send(lea, f"lea {index}")
        _send(ben, f"ben {index}")

    page = _history(lea, "?limit=4").json()

    assert [m["body"] for m in page["messages"]] == ["lea 1", "ben 1", "lea 2", "ben 2"]
    assert page["has_more"] is True

    oldest = page["messages"][0]["position"]
    previous = _history(lea, f"?limit=4&before={oldest}").json()
    assert [m["body"] for m in previous["messages"]] == ["lea 0", "ben 0"]
    assert previous["has_more"] is False


def test_history_bounds_are_validated(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    assert _history(lea, "?limit=0").status_code == 422
    assert _history(lea, "?limit=101").status_code == 422
    assert _history(lea, "?before=0").status_code == 422


# --- US-013 · CA6 à CA8 : ses propres messages ------------------------------------------


def test_author_edits_own_message(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    message_id = _send(lea, "Premier jet").json()["id"]

    response = lea.request("PATCH", f"/api/chat/messages/{message_id}", json={"body": "Corrigé"})

    assert response.status_code == 200
    assert response.json()["body"] == "Corrigé"
    assert response.json()["edited"] is True


def test_author_deletes_own_message_and_a_trace_remains(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    message_id = _send(lea).json()["id"]

    response = lea.request("DELETE", f"/api/chat/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["body"] is None
    assert response.json()["deleted_by"] == "player"
    kept = _history(lea).json()["messages"]
    assert [m["id"] for m in kept] == [message_id]


def test_player_cannot_touch_the_message_of_another_player(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    message_id = _send(lea, "Intact").json()["id"]

    edited = ben.request("PATCH", f"/api/chat/messages/{message_id}", json={"body": "Piraté"})
    deleted = ben.request("DELETE", f"/api/chat/messages/{message_id}")

    assert edited.status_code == deleted.status_code == 403
    assert error_code(edited) == "forbidden"
    assert _history(lea).json()["messages"][0]["body"] == "Intact"


def test_player_cannot_touch_a_gm_message(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    message_id = _send(gm).json()["id"]

    assert lea.request("DELETE", f"/api/chat/messages/{message_id}").status_code == 403


# --- US-030 : modération par le MJ ------------------------------------------------------


def test_gm_edits_and_deletes_any_message(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    edited_id = _send(lea, "À corriger").json()["id"]
    deleted_id = _send(lea, "À retirer").json()["id"]

    edited = gm.request("PATCH", f"/api/chat/messages/{edited_id}", json={"body": "Corrigé"})
    deleted = gm.request("DELETE", f"/api/chat/messages/{deleted_id}")

    assert edited.json()["body"] == "Corrigé"
    assert edited.json()["edited"] is True
    assert edited.json()["author"]["display_name"] == "lea.vale"
    assert deleted.json()["deleted_by"] == "gm"
    assert deleted.json()["body"] is None


def test_deleted_message_cannot_be_edited_and_deleting_twice_is_harmless(
    ctx: TestContext,
) -> None:
    lea = player(ctx, "lea.vale")
    message_id = _send(lea).json()["id"]
    lea.request("DELETE", f"/api/chat/messages/{message_id}")

    edited = lea.request("PATCH", f"/api/chat/messages/{message_id}", json={"body": "Retour"})
    deleted_again = lea.request("DELETE", f"/api/chat/messages/{message_id}")

    assert edited.status_code == 409
    assert error_code(edited) == "message_deleted"
    assert deleted_again.status_code == 200
    assert deleted_again.json()["deleted_by"] == "player"


def test_unknown_message_is_not_found(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("DELETE", f"/api/chat/messages/{uuid4()}")

    assert response.status_code == 404
    assert error_code(response) == "not_found"
