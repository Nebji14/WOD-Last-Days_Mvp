"""Éléments d'une fiche : spécialités, moralité, listes, tactiques, expérience, notes."""

from typing import Any

from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.api.test_characters import create, rule
from tests.conftest import TestContext


def _sheet(character: dict[str, Any], index: int = 0) -> dict[str, Any]:
    sheet: dict[str, Any] = character["sheets"][index]
    return sheet


def _set_total(actor: Actor, character_id: str, field: str, value: int, expected: int) -> Response:
    return actor.request(
        "PATCH",
        f"/api/characters/{character_id}",
        json={"field": field, "value": value, "expected": expected},
    )


def _spend(actor: Actor, character_id: str, points: int, tactical: bool = False) -> Response:
    return actor.request(
        "POST",
        f"/api/characters/{character_id}/xp-expenses",
        json={"is_tactical": tactical, "points": points, "justification": "Armes à feu 3 → 4"},
    )


# --- Spécialités --------------------------------------------------------


def test_specialty_field_is_split_on_commas_and_emptied_by_an_empty_text(
    ctx: TestContext,
) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]
    path = f"/api/sheets/{sheet_id}/specialties/firearms"

    filled = lea.request("PUT", path, json={"text": "Fusil,  Pistolet , fusil"}).json()
    emptied = lea.request("PUT", path, json={"text": "  "}).json()

    assert _sheet(filled)["specialties"]["firearms"] == ["Fusil", "Pistolet"]
    assert "firearms" not in _sheet(emptied)["specialties"]
    assert _sheet(emptied)["specialties"]["occult"] == ["Rituels", "Démons"]


def test_specialty_on_an_unknown_skill_is_refused(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]

    response = lea.request("PUT", f"/api/sheets/{sheet_id}/specialties/owner", json={"text": "x"})

    assert response.status_code == 422


# --- Annotations de moralité --------------------------------------------


def test_morality_notes_keep_the_level_where_they_were_acquired(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]

    added = lea.request(
        "POST",
        f"/api/sheets/{sheet_id}/morality-notes",
        json={"level": 6, "body": "Insomnie"},
    )
    note = _sheet(added.json())["morality_notes"][0]
    edited = lea.request(
        "PATCH", f"/api/morality-notes/{note['id']}", json={"level": 5, "body": "Paranoïa"}
    ).json()
    removed = lea.request("DELETE", f"/api/morality-notes/{note['id']}").json()

    assert added.status_code == 201
    assert (note["level"], note["body"]) == (6, "Insomnie")
    assert _sheet(edited)["morality_notes"] == [{"id": note["id"], "level": 5, "body": "Paranoïa"}]
    assert _sheet(removed)["morality_notes"] == []


def test_morality_note_level_is_bounded(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]

    response = lea.request(
        "POST", f"/api/sheets/{sheet_id}/morality-notes", json={"level": 11, "body": "x"}
    )

    assert error_code(response) == "validation_error"


# --- Atouts, handicaps, pouvoirs, objets, armes, armures ----------------


def test_entry_keeps_only_the_fields_of_its_kind(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]
    weapon = {
        "kind": "weapon", "name": "Fusil à pompe", "damage_modifier": 4, "range": "20/40/80",
        "size": 2, "initiative_penalty": -3, "description": "Calibre 12", "level": 3,
        "quantity": 9,
    }  # fmt: skip

    lea.request("POST", f"/api/sheets/{sheet_id}/entries", json=weapon)
    lea.request("POST", f"/api/sheets/{sheet_id}/entries", json={"kind": "merit", "name": "Allié"})
    entries = _sheet(
        lea.request(
            "POST",
            f"/api/sheets/{sheet_id}/entries",
            json={"kind": "flaw", "name": "Boiteux"},
        ).json()
    )["entries"]

    stored_weapon, merit, flaw = entries
    assert stored_weapon["damage_modifier"] == 4
    assert stored_weapon["range"] == "20/40/80"
    assert (stored_weapon["level"], stored_weapon["quantity"]) == (None, None)
    assert merit["level"] == 1  # un atout a toujours un niveau
    assert flaw["level"] is None  # facultatif pour un handicap


def test_entry_is_edited_in_place_and_deleted(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]
    created = lea.request(
        "POST",
        f"/api/sheets/{sheet_id}/entries",
        json={"kind": "item", "name": "Lampe", "quantity": 1},
    ).json()
    entry_id = _sheet(created)["entries"][0]["id"]

    edited = lea.request(
        "PATCH", f"/api/entries/{entry_id}", json={"name": "Lampe torche", "quantity": 2}
    ).json()
    removed = lea.request("DELETE", f"/api/entries/{entry_id}").json()

    assert _sheet(edited)["entries"][0]["name"] == "Lampe torche"
    assert _sheet(edited)["entries"][0]["quantity"] == 2
    assert _sheet(edited)["entries"][0]["kind"] == "item"
    assert _sheet(removed)["entries"] == []


def test_entry_values_are_bounded(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = _sheet(create(lea))["id"]

    response = lea.request(
        "POST", f"/api/sheets/{sheet_id}/entries", json={"kind": "merit", "level": 99}
    )

    assert error_code(response) == "validation_error"


# --- Tactiques partagées ---------------------------------------------------


def test_tactic_is_shared_between_sheets_and_survives_until_the_last_one_drops_it(
    ctx: TestContext,
) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    lea_sheet = _sheet(create(lea))["id"]
    ben_sheet = _sheet(create(ben))["id"]

    created = lea.request(
        "POST", f"/api/sheets/{lea_sheet}/tactics", json={"name": "Tenaille", "description": ""}
    ).json()
    tactic_id = _sheet(created)["tactics"][0]["id"]
    available = ben.request("GET", "/api/tactics").json()["tactics"]
    ben.request("POST", f"/api/sheets/{ben_sheet}/tactics", json={"tactic_id": tactic_id})
    ben.request(
        "PATCH",
        f"/api/sheets/{ben_sheet}/tactics/{tactic_id}",
        json={"name": "Tenaille", "description": "Deux angles d'attaque"},
    )

    assert [t["name"] for t in available] == ["Tenaille"]
    seen_by_lea = _sheet(lea.request("GET", "/api/characters").json()["characters"][0])
    assert seen_by_lea["tactics"][0]["description"] == "Deux angles d'attaque"

    lea.request("DELETE", f"/api/sheets/{lea_sheet}/tactics/{tactic_id}")
    assert len(ben.request("GET", "/api/tactics").json()["tactics"]) == 1
    ben.request("DELETE", f"/api/sheets/{ben_sheet}/tactics/{tactic_id}")
    assert ben.request("GET", "/api/tactics").json()["tactics"] == []


def test_tactic_can_only_be_edited_from_a_sheet_that_knows_it(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    lea_sheet = _sheet(create(lea))["id"]
    ben_sheet = _sheet(create(ben))["id"]
    created = lea.request(
        "POST", f"/api/sheets/{lea_sheet}/tactics", json={"name": "Tenaille"}
    ).json()
    tactic_id = _sheet(created)["tactics"][0]["id"]

    response = ben.request(
        "PATCH", f"/api/sheets/{ben_sheet}/tactics/{tactic_id}", json={"name": "Piraté"}
    )

    assert response.status_code == 404


# --- Expérience ------------------------------------------------


def test_expense_lowers_the_balance_and_never_the_total(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    _set_total(lea, character_id, "xp_general_total", 10, 0)
    _set_total(lea, character_id, "xp_tactical_total", 4, 0)

    spent = _spend(lea, character_id, 6).json()

    assert spent["xp_general"] == {"total": 10, "balance": 4}
    # L'expérience tactique est suivie à part.
    assert spent["xp_tactical"] == {"total": 4, "balance": 4}
    assert [(e["points"], e["is_tactical"]) for e in spent["expenses"]] == [(6, False)]


def test_expense_needs_enough_balance_and_a_justification(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    _set_total(lea, character_id, "xp_general_total", 5, 0)

    too_much = _spend(lea, character_id, 6)
    wrong_pool = _spend(lea, character_id, 1, tactical=True)
    unjustified = lea.request(
        "POST",
        f"/api/characters/{character_id}/xp-expenses",
        json={"is_tactical": False, "points": 1, "justification": "   "},
    )

    assert rule(too_much) == rule(wrong_pool) == "xp_insufficient"
    assert error_code(unjustified) == "validation_error"


def test_total_cannot_drop_below_what_was_spent(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    _set_total(lea, character_id, "xp_general_total", 10, 0)
    _spend(lea, character_id, 6)

    response = _set_total(lea, character_id, "xp_general_total", 5, 10)

    assert response.status_code == 422
    assert rule(response) == "xp_total_below_spent"


def test_expense_can_be_corrected_within_the_balance_or_deleted(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    _set_total(lea, character_id, "xp_general_total", 10, 0)
    expense_id = _spend(lea, character_id, 6).json()["expenses"][0]["id"]

    too_much = lea.request(
        "PATCH", f"/api/xp-expenses/{expense_id}", json={"points": 11, "justification": "x"}
    )
    corrected = lea.request(
        "PATCH", f"/api/xp-expenses/{expense_id}", json={"points": 10, "justification": "Corrigé"}
    ).json()
    removed = lea.request("DELETE", f"/api/xp-expenses/{expense_id}").json()

    assert rule(too_much) == "xp_insufficient"
    assert corrected["xp_general"] == {"total": 10, "balance": 0}
    assert removed["xp_general"] == {"total": 10, "balance": 10}


def test_gm_spends_experience_like_the_owner(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]

    _set_total(gm, character_id, "xp_general_total", 3, 0)

    assert _spend(gm, character_id, 2).json()["xp_general"]["balance"] == 1


# --- Notes de la fiche -------------------------------------------------------------


def test_owner_manages_notes_and_the_gm_only_reads_them(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]

    created = lea.request("POST", f"/api/characters/{character_id}/notes").json()
    note_id = created["note_id"]
    lea.request("PATCH", f"/api/notes/{note_id}", json={"title": "Piste", "body": "Le quai 9."})
    seen_by_gm = gm.request("GET", f"/api/characters/{character_id}").json()

    assert created["character"]["notes"][0]["title"] == "Sans titre"
    assert created["character"]["can_manage_notes"] is True
    assert seen_by_gm["can_manage_notes"] is False
    assert [(n["title"], n["body"]) for n in seen_by_gm["notes"]] == [("Piste", "Le quai 9.")]

    refusals = [
        gm.request("POST", f"/api/characters/{character_id}/notes"),
        gm.request("PATCH", f"/api/notes/{note_id}", json={"title": "x", "body": "y"}),
        gm.request("DELETE", f"/api/notes/{note_id}"),
    ]
    assert [r.status_code for r in refusals] == [403, 403, 403]

    removed = lea.request("DELETE", f"/api/notes/{note_id}").json()
    assert removed["notes"] == []


def test_another_player_cannot_reach_any_item(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    character = create(lea)
    sheet_id = _sheet(character)["id"]
    note_id = lea.request("POST", f"/api/characters/{character['id']}/notes").json()["note_id"]
    entry = lea.request(
        "POST", f"/api/sheets/{sheet_id}/entries", json={"kind": "item", "name": "Clé"}
    ).json()
    entry_id = _sheet(entry)["entries"][0]["id"]

    attempts = [
        ben.request("PUT", f"/api/sheets/{sheet_id}/specialties/firearms", json={"text": "x"}),
        ben.request("PATCH", f"/api/entries/{entry_id}", json={"name": "Volé"}),
        ben.request("DELETE", f"/api/entries/{entry_id}"),
        ben.request("PATCH", f"/api/notes/{note_id}", json={"title": "x", "body": "y"}),
        ben.request("DELETE", f"/api/notes/{note_id}"),
        _spend(ben, character["id"], 1),
        ben.request("POST", f"/api/sheets/{sheet_id}/tactics", json={"name": "x"}),
    ]

    assert [a.status_code for a in attempts] == [404] * 7
