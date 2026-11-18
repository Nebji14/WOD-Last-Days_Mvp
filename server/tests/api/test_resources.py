"""Ressources libres : ajout, modification, suppression, droits et dépense par un pouvoir."""

from typing import Any

from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.api.test_characters import create, rule
from tests.api.test_npcs import new_npc
from tests.conftest import TestContext


def add(
    actor: Actor, character: dict[str, Any], name: str = "Mana", max_value: int = 5
) -> Response:
    return actor.request(
        "POST",
        f"/api/characters/{character['id']}/resources",
        json={"name": name, "max_value": max_value},
    )


def patch(
    actor: Actor, resource: dict[str, Any], field: str, value: Any, expected: Any
) -> Response:
    return actor.request(
        "PATCH",
        f"/api/resources/{resource['id']}",
        json={"field": field, "value": value, "expected": expected},
    )


def mana(actor: Actor, character: dict[str, Any], max_value: int = 5) -> dict[str, Any]:
    response = add(actor, character, max_value=max_value)
    assert response.status_code == 201, response.text
    resource: dict[str, Any] = response.json()["resources"][-1]
    return resource


def test_resource_starts_full_and_is_shared_by_every_form(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)

    resource = mana(lea, isaac)

    assert (resource["name"], resource["max_value"], resource["current_value"]) == ("Mana", 5, 5)
    form = lea.request("POST", f"/api/characters/{isaac['id']}/forms", json={"form_name": "Loup"})
    assert form.status_code == 201, form.text
    assert len(form.json()["resources"]) == 1


def test_resource_is_adjusted_like_willpower(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    resource = mana(lea, create(lea))

    spent = patch(lea, resource, "current_value", 2, 5).json()["resources"][0]
    lowered = patch(lea, spent, "max_value", 1, 5).json()["resources"][0]
    renamed = patch(lea, lowered, "name", " Douleur ", "Mana").json()["resources"][0]

    assert spent["current_value"] == 2
    assert (lowered["max_value"], lowered["current_value"]) == (1, 1)
    assert renamed["name"] == "Douleur"


def test_resource_rules_are_enforced(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    resource = mana(lea, isaac)

    above = patch(lea, resource, "current_value", 6, 5)
    taken = add(lea, isaac, name="MANA")
    unknown = patch(lea, resource, "kind", 1, 1)

    assert rule(above) == "resource_above_max"
    assert rule(taken) == "resource_name_taken"
    assert rule(unknown) == "unknown_field"


def test_concurrent_change_is_never_overwritten(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    resource = mana(lea, create(lea))
    patch(lea, resource, "current_value", 4, 5)

    stale = patch(lea, resource, "current_value", 3, 5)

    assert stale.status_code == 409
    assert error_code(stale) == "edit_conflict"


def test_resource_is_deleted(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    resource = mana(lea, create(lea))

    response = lea.request("DELETE", f"/api/resources/{resource['id']}")

    assert response.status_code == 200
    assert response.json()["resources"] == []


def test_gm_manages_resources_of_players_and_npcs(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    gm = game_master(ctx)

    assert add(gm, create(lea)).status_code == 201
    assert add(gm, new_npc(gm)).status_code == 201


def test_other_player_cannot_touch_resources(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    tom = player(ctx, "tom")
    isaac = create(lea)
    resource = mana(lea, isaac)

    assert add(tom, isaac).status_code == 404
    assert patch(tom, resource, "current_value", 1, 5).status_code == 404
    assert tom.request("DELETE", f"/api/resources/{resource['id']}").status_code == 404


# --- Dépense par un pouvoir --------------------------------------------------------------


def _power(actor: Actor, character: dict[str, Any], **recipe: Any) -> Response:
    sheet_id = character["sheets"][0]["id"]
    payload = {"kind": "power", "name": "Trait de mana", "roll": {"parts": ["wits"], **recipe}}
    return actor.request("POST", f"/api/sheets/{sheet_id}/entries", json=payload)


def _roll_power(actor: Actor, character: dict[str, Any], entry_id: str) -> Response:
    payload = {
        "kind": "entry",
        "character_id": character["id"],
        "sheet_id": character["sheets"][0]["id"],
        "entry_id": entry_id,
    }
    return actor.request("POST", "/api/dice/rolls", json=payload)


def _reload(actor: Actor, character: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = actor.request("GET", f"/api/characters/{character['id']}").json()
    return data


def test_power_spends_its_resource_and_willpower_together(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    resource = mana(lea, isaac)
    willpower = isaac["sheets"][0]["willpower_current"]
    sheet = _power(lea, isaac, willpower_cost=1, resource_id=resource["id"], resource_cost=2)
    entry = sheet.json()["sheets"][0]["entries"][-1]

    assert _roll_power(lea, isaac, entry["id"]).status_code == 201

    after = _reload(lea, isaac)
    assert after["resources"][0]["current_value"] == 3
    assert after["sheets"][0]["willpower_current"] == willpower - 1


def test_power_is_refused_without_enough_resource_and_spends_nothing(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    resource = mana(lea, isaac, max_value=1)
    willpower = isaac["sheets"][0]["willpower_current"]
    sheet = _power(lea, isaac, willpower_cost=1, resource_id=resource["id"], resource_cost=2)
    entry = sheet.json()["sheets"][0]["entries"][-1]

    response = _roll_power(lea, isaac, entry["id"])

    assert rule(response) == "no_resource"
    assert _reload(lea, isaac)["sheets"][0]["willpower_current"] == willpower


def test_recipe_cannot_spend_a_resource_of_another_character(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    other = mana(lea, create(lea))

    response = _power(lea, isaac, resource_id=other["id"], resource_cost=1)

    assert rule(response) == "recipe_resource"


def test_deleting_a_resource_removes_its_cost_from_powers(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    resource = mana(lea, isaac)
    _power(lea, isaac, resource_id=resource["id"], resource_cost=2)

    after = lea.request("DELETE", f"/api/resources/{resource['id']}").json()

    recipe = after["sheets"][0]["entries"][-1]["roll"]
    assert (recipe["resource_id"], recipe["resource_cost"]) == (None, 0)
