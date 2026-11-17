"""Outil Joueurs du MJ (04a) : liste des joueurs (US-025) et éveil (04a-I5)."""

from uuid import uuid4

from tests.api.helpers import error_code, game_master, player
from tests.api.test_characters import create, patch_sheet
from tests.conftest import TestContext

# --- Liste des joueurs (US-025) ---------------------------------------------------------


def test_gm_sees_every_player_with_or_without_character(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    player(ctx, "tom")
    create(lea)
    create(lea, identity={"name": "Silas Crane"})

    response = gm.request("GET", "/api/players")

    assert response.status_code == 200
    players = {p["username"]: p for p in response.json()["players"]}
    assert set(players) == {"lea.vale", "tom"}
    assert players["lea.vale"]["character_names"] == ["Isaac Thorne", "Silas Crane"]
    assert players["tom"]["character_names"] == []
    assert players["tom"]["online"] is False
    assert players["tom"]["status"] == "active"
    assert "auth_email" not in players["tom"]


def test_player_list_is_reserved_to_the_gm(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = lea.request("GET", "/api/players")

    assert response.status_code == 403
    assert error_code(response) == "forbidden"


# --- Éveil (04a-I5, notes 05 ÉVEIL) -----------------------------------------------------


def test_gm_awakens_a_character_and_its_attributes_can_reach_ten(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)
    sheet_id = character["sheets"][0]["id"]

    response = gm.request("POST", f"/api/characters/{character['id']}/awaken")

    assert response.status_code == 200
    assert response.json()["awakened_at"] is not None
    assert lea.request("GET", f"/api/characters/{character['id']}").json()["awakened"] is True
    assert patch_sheet(lea, sheet_id, "strength", 8, 2).status_code == 200


def test_awakening_twice_keeps_the_first_date(ctx: TestContext) -> None:
    gm = game_master(ctx)
    character_id = create(player(ctx, "lea.vale"))["id"]
    path = f"/api/characters/{character_id}/awaken"

    first = gm.request("POST", path).json()["awakened_at"]
    second = gm.request("POST", path).json()["awakened_at"]

    assert first == second


def test_player_cannot_awaken_and_gets_no_hint(ctx: TestContext) -> None:
    game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)

    response = lea.request("POST", f"/api/characters/{character['id']}/awaken")

    assert response.status_code == 404
    assert error_code(response) == "not_found"
    assert "awaken" not in response.text.lower()
    assert "awakened" not in lea.request("GET", f"/api/characters/{character['id']}").json()


def test_awakening_an_unknown_character_is_not_found(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request("POST", f"/api/characters/{uuid4()}/awaken")

    assert response.status_code == 404
