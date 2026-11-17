"""Outil PNJ et feuille de PNJ : création, modification, catégories, suppression, droits."""

from typing import Any

from tests.api.helpers import Actor, error_code, game_master, player
from tests.api.test_characters import create, patch_sheet
from tests.conftest import TestContext


def new_npc(gm: Actor, model: str = "simplified", **extra: Any) -> dict[str, Any]:
    response = gm.request("POST", "/api/npcs", json={"model": model, **extra})
    assert response.status_code == 201, response.text
    npc: dict[str, Any] = response.json()
    return npc


def set_field(gm: Actor, npc_id: str, field: str, value: Any, expected: Any = None) -> Any:
    return gm.request(
        "PATCH", f"/api/npcs/{npc_id}", json={"field": field, "value": value, "expected": expected}
    )


def directory(gm: Actor) -> dict[str, Any]:
    data: dict[str, Any] = gm.request("GET", "/api/npcs").json()
    return data


# --- Création et liste ---------------------------------------------------


def test_gm_creates_a_blank_simplified_npc_without_owner(ctx: TestContext) -> None:
    gm = game_master(ctx)

    npc = new_npc(gm)

    assert npc["owner_id"] is None
    assert npc["npc"]["model"] == "simplified"
    assert (npc["npc"]["power"], npc["npc"]["finesse"], npc["npc"]["resilience"]) == (1, 1, 1)
    assert npc["sheets"][0]["texts"]["name"] == "Nouveau PNJ"
    [card] = directory(gm)["npcs"]
    assert (card["id"], card["model"]) == (npc["id"], "simplified")


def test_full_npc_has_no_simplified_traits(ctx: TestContext) -> None:
    gm = game_master(ctx)

    npc = new_npc(gm, "full")

    assert npc["npc"]["power"] is None
    assert set_field(gm, npc["id"], "power", 4, None).status_code == 422


def test_npcs_are_reserved_to_the_gm(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    npc_id = new_npc(gm)["id"]

    assert lea.request("GET", "/api/npcs").status_code == 403
    assert lea.request("POST", "/api/npcs", json={"model": "full"}).status_code == 403
    assert lea.request("GET", f"/api/characters/{npc_id}").status_code == 404
    assert lea.request("DELETE", f"/api/npcs/{npc_id}").status_code == 403


def test_player_lists_do_not_include_npcs(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    create(lea)
    new_npc(gm)

    assert len(lea.request("GET", "/api/characters").json()["characters"]) == 1
    [row] = gm.request("GET", "/api/players").json()["players"]
    assert row["character_names"] == ["Isaac Thorne"]


# --- Modification ----------------------------------------------


def test_simplified_traits_stay_between_one_and_ten(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc_id = new_npc(gm)["id"]

    raised = set_field(gm, npc_id, "power", 10, 1)
    too_high = set_field(gm, npc_id, "finesse", 11, 1)
    zero = set_field(gm, npc_id, "resilience", 0, 1)

    assert raised.json()["npc"]["power"] == 10
    assert too_high.status_code == 422
    assert zero.status_code == 422


def test_simplified_npc_has_no_attributes_or_skills(ctx: TestContext) -> None:
    gm = game_master(ctx)
    sheet_id = new_npc(gm)["sheets"][0]["id"]

    assert patch_sheet(gm, sheet_id, "strength", 3, 1).status_code == 422
    assert patch_sheet(gm, sheet_id, "firearms", 2, 0).status_code == 422
    specialty = gm.request(
        "PUT", f"/api/sheets/{sheet_id}/specialties/firearms", json={"text": "Fusil"}
    )
    assert specialty.status_code == 422


def test_full_npc_attributes_are_free_up_to_ten(ctx: TestContext) -> None:
    gm = game_master(ctx)
    sheet_id = new_npc(gm, "full")["sheets"][0]["id"]

    assert patch_sheet(gm, sheet_id, "strength", 8, 1).status_code == 200
    assert patch_sheet(gm, sheet_id, "strength", 11, 8).status_code == 422


def test_health_and_willpower_max_are_set_freely(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc = new_npc(gm)
    sheet = npc["sheets"][0]

    response = patch_sheet(gm, sheet["id"], "health_max", 12, sheet["effective"]["health_max"])

    assert response.status_code == 200
    assert response.json()["sheets"][0]["effective"]["health_max"] == 12


def test_npc_notes_refuse_a_concurrent_overwrite(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc_id = new_npc(gm)["id"]

    assert set_field(gm, npc_id, "notes", "Veuve d'un pêcheur.", "").status_code == 200
    stale = set_field(gm, npc_id, "notes", "Autre texte", "")

    assert stale.status_code == 409
    assert error_code(stale) == "edit_conflict"


def test_npc_refuses_experience_tactics_forms_and_awakening(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc = new_npc(gm, "full")
    npc_id, sheet_id = npc["id"], npc["sheets"][0]["id"]

    xp = gm.request(
        "PATCH",
        f"/api/characters/{npc_id}",
        json={"field": "xp_general_total", "value": 5, "expected": 0},
    )
    expense = gm.request(
        "POST",
        f"/api/characters/{npc_id}/xp-expenses",
        json={"is_tactical": False, "points": 1, "justification": "x"},
    )
    tactic = gm.request("POST", f"/api/sheets/{sheet_id}/tactics", json={"name": "Embuscade"})
    form = gm.request("POST", f"/api/characters/{npc_id}/forms", json={"form_name": "Loup"})
    awaken = gm.request("POST", f"/api/characters/{npc_id}/awaken")

    for refused in (xp, expense, tactic, form):
        assert refused.status_code == 422, refused.text
        assert refused.json()["error"]["details"][0]["rule"] == "npc_feature"
    assert awaken.status_code == 404


# --- Catégories -----------------------------------------------------


def test_npc_moves_to_a_category_and_up_when_it_is_deleted(ctx: TestContext) -> None:
    gm = game_master(ctx)
    villains = gm.request("POST", "/api/npc-categories", json={"name": "Antagonistes"}).json()
    cult = gm.request(
        "POST", "/api/npc-categories", json={"name": "Culte", "parent_id": villains["id"]}
    ).json()
    npc = new_npc(gm, category_id=cult["id"])

    assert gm.request("DELETE", f"/api/npc-categories/{cult['id']}").status_code == 204

    [card] = directory(gm)["npcs"]
    assert card["id"] == npc["id"]
    assert card["category_id"] == villains["id"]


def test_category_field_moves_the_npc(ctx: TestContext) -> None:
    gm = game_master(ctx)
    allies = gm.request("POST", "/api/npc-categories", json={"name": "Alliés"}).json()
    npc_id = new_npc(gm)["id"]

    moved = set_field(gm, npc_id, "category_id", allies["id"])
    back = set_field(gm, npc_id, "category_id", None)

    assert moved.json()["npc"]["category_id"] == allies["id"]
    assert back.json()["npc"]["category_id"] is None


def test_category_cannot_move_into_its_own_subcategory(ctx: TestContext) -> None:
    gm = game_master(ctx)
    parent = gm.request("POST", "/api/npc-categories", json={"name": "Alliés"}).json()["id"]
    child = gm.request(
        "POST", "/api/npc-categories", json={"name": "Contacts", "parent_id": parent}
    ).json()["id"]

    response = gm.request("PUT", f"/api/npc-categories/{parent}/parent", json={"parent_id": child})

    assert response.status_code == 422
    assert error_code(response) == "folder_cycle"


# --- Suppression -----------------------------------------------------------------


def test_deleted_npc_disappears(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc_id = new_npc(gm)["id"]

    assert gm.request("DELETE", f"/api/npcs/{npc_id}").status_code == 204

    assert directory(gm)["npcs"] == []
    assert gm.request("GET", f"/api/characters/{npc_id}").status_code == 404


def test_player_character_cannot_be_deleted_as_an_npc(ctx: TestContext) -> None:
    gm = game_master(ctx)
    character_id = create(player(ctx, "lea.vale"))["id"]

    assert gm.request("DELETE", f"/api/npcs/{character_id}").status_code == 404
