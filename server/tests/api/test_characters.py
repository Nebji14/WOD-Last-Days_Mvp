"""Routes des personnages : création, lecture, modification, droits et secret de l'éveil."""

from typing import Any
from uuid import UUID, uuid4

from httpx import Response

from app.domain.traits import SKILL_NAMES
from tests.api.helpers import Actor, error_code, game_master, player
from tests.conftest import TestContext


def creation_payload(**overrides: Any) -> dict[str, Any]:
    """Saisie valide de l'assistant : attributs 5/4/3, compétences 11/7/4, 3 spécialités."""
    payload: dict[str, Any] = {
        "identity": {"name": "Isaac Thorne", "concept": "Chasseur de primes"},
        "attribute_priorities": {"mental": 1, "physical": 2, "social": 3},
        "attributes": {
            "intelligence": 3, "wits": 3, "resolve": 2,
            "strength": 2, "dexterity": 3, "stamina": 2,
            "presence": 2, "manipulation": 2, "composure": 2,
        },
        "skill_priorities": {"mental": 1, "physical": 2, "social": 3},
        "skills": dict.fromkeys(SKILL_NAMES, 0) | {
            "academics": 3, "investigation": 3, "occult": 3, "medicine": 2,
            "athletics": 2, "firearms": 3, "stealth": 2,
            "empathy": 2, "streetwise": 2,
        },
        "specialties": [
            {"skill": "firearms", "label": "Fusil"},
            {"skill": "occult", "label": "Rituels"},
            {"skill": "occult", "label": "Démons"},
        ],
    }  # fmt: skip
    return payload | overrides


def create(actor: Actor, **overrides: Any) -> dict[str, Any]:
    response = actor.request("POST", "/api/characters", json=creation_payload(**overrides))
    assert response.status_code == 201, response.text
    character: dict[str, Any] = response.json()
    return character


def patch_sheet(actor: Actor, sheet_id: str, field: str, value: Any, expected: Any) -> Response:
    return actor.request(
        "PATCH",
        f"/api/sheets/{sheet_id}",
        json={"field": field, "value": value, "expected": expected},
    )


def rule(response: Response) -> str:
    return str(response.json()["error"]["details"][0]["rule"])


# --- Création ------------------------------------------------------------------------


def test_created_character_starts_in_the_initial_state(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    character = create(lea)
    sheet = character["sheets"][0]

    assert character["owner_id"] == str(lea.account_id)
    assert character["is_played"] is True
    assert sheet["is_main"] is True
    assert sheet["texts"]["name"] == "Isaac Thorne"
    # La base calculée est proposée comme valeur effective.
    assert sheet["base"] == {
        "size": 5, "speed": 10, "defense": 5, "initiative": 5, "health_max": 7, "willpower_max": 4
    }  # fmt: skip
    assert sheet["effective"] == sheet["base"]
    # Piste vide, volonté pleine, moralité à 7, expérience à zéro.
    assert sheet["wound_track"] == ""
    assert sheet["willpower_current"] == 4
    assert sheet["morality"] == 7
    assert character["xp_general"] == {"total": 0, "balance": 0}
    assert character["xp_tactical"] == {"total": 0, "balance": 0}
    assert sheet["specialties"] == {"firearms": ["Fusil"], "occult": ["Rituels", "Démons"]}


def test_creation_keeps_effective_values_chosen_at_the_last_step(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    sheet = create(lea, effective={"speed": 12, "health_max": 8})["sheets"][0]

    assert (sheet["effective"]["speed"], sheet["base"]["speed"]) == (12, 10)
    assert (sheet["effective"]["health_max"], sheet["base"]["health_max"]) == (8, 7)


def test_creation_rejects_a_sheet_breaking_the_rules(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    attributes = creation_payload()["attributes"] | {"resolve": 1}

    response = lea.request(
        "POST",
        "/api/characters",
        json=creation_payload(attributes=attributes, specialties=[]),
    )

    assert response.status_code == 422
    assert error_code(response) == "rule_violation"
    assert response.json()["error"]["details"] == [
        {"rule": "attribute_budget", "field": "mental"},
        {"rule": "specialty_count"},
    ]


def test_creation_requires_every_trait_and_a_name(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    incomplete = {k: v for k, v in creation_payload()["skills"].items() if k != "drive"}

    missing_skill = lea.request("POST", "/api/characters", json=creation_payload(skills=incomplete))
    no_name = lea.request(
        "POST", "/api/characters", json=creation_payload(identity={"name": "   "})
    )

    assert error_code(missing_skill) == error_code(no_name) == "validation_error"


def test_gm_has_no_character(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request("POST", "/api/characters", json=creation_payload())

    assert response.status_code == 403


# --- Consultation et droits ---------------------------------------------------------


def test_owner_and_gm_read_the_sheet_but_not_another_player(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    character_id = create(lea)["id"]

    assert lea.request("GET", f"/api/characters/{character_id}").status_code == 200
    assert gm.request("GET", f"/api/characters/{character_id}").status_code == 200
    refused = ben.request("GET", f"/api/characters/{character_id}")
    assert refused.status_code == 404
    assert ctx.client.get(f"/api/characters/{character_id}").status_code == 401


def test_listing_is_limited_to_own_characters_except_for_the_gm(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    create(lea)

    mine = lea.request("GET", "/api/characters").json()["characters"]
    theirs = ben.request("GET", f"/api/characters?owner={lea.account_id}")
    seen_by_gm = gm.request("GET", f"/api/characters?owner={lea.account_id}").json()

    assert len(mine) == 1
    assert theirs.status_code == 403
    assert len(seen_by_gm["characters"]) == 1
    assert ben.request("GET", "/api/characters").json()["characters"] == []


def test_another_player_cannot_modify_the_sheet(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ben = player(ctx, "ben.ard")
    character = create(lea)
    sheet_id = character["sheets"][0]["id"]

    attempts = [
        patch_sheet(ben, sheet_id, "strength", 5, 2),
        ben.request("DELETE", f"/api/characters/{character['id']}"),
        ben.request("POST", f"/api/characters/{character['id']}/play"),
        ben.request(
            "POST",
            f"/api/sheets/{sheet_id}/wounds",
            json={"action": "add", "wound": "*", "expected": ""},
        ),
        ben.request(
            "POST", f"/api/sheets/{sheet_id}/entries", json={"kind": "item", "name": "Clé"}
        ),
    ]

    assert [a.status_code for a in attempts] == [404] * 5
    untouched = lea.request("GET", f"/api/characters/{character['id']}").json()
    assert untouched["sheets"][0] == character["sheets"][0]


# --- Modification champ par champ ---------------------------------------------------


def test_field_is_saved_alone_and_base_values_follow(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet = create(lea)["sheets"][0]

    updated = patch_sheet(lea, sheet["id"], "strength", 4, 2).json()["sheets"][0]

    assert updated["attributes"]["strength"] == 4
    # La base est recalculée, la valeur effective saisie ne bouge pas.
    assert updated["base"]["speed"] == 12
    assert updated["effective"]["speed"] == 10


def test_gm_edits_with_the_same_possibilities_as_the_owner(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    sheet = create(lea)["sheets"][0]

    response = patch_sheet(gm, sheet["id"], "concept", "Traqueur", "Chasseur de primes")

    assert response.status_code == 200
    assert response.json()["sheets"][0]["texts"]["concept"] == "Traqueur"


def test_concurrent_edit_is_never_overwritten_silently(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    sheet = create(lea)["sheets"][0]
    patch_sheet(gm, sheet["id"], "morality", 6, 7)

    stale = patch_sheet(lea, sheet["id"], "morality", 8, 7)

    assert stale.status_code == 409
    assert error_code(stale) == "edit_conflict"
    current = lea.request("GET", "/api/characters").json()["characters"][0]["sheets"][0]
    assert current["morality"] == 6


def test_values_outside_the_rules_are_refused(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet = create(lea)["sheets"][0]
    sheet_id = sheet["id"]

    refusals = {
        "attribut au-dessus de 5": patch_sheet(lea, sheet_id, "strength", 6, 2),
        "attribut sous 1": patch_sheet(lea, sheet_id, "strength", 0, 2),
        "compétence au-dessus de 5": patch_sheet(lea, sheet_id, "firearms", 6, 3),
        "moralité hors de 1 à 10": patch_sheet(lea, sheet_id, "morality", 11, 7),
        "volonté au-dessus du maximum": patch_sheet(
            lea, sheet_id, "willpower_current", 5, 4
        ),
        "volonté maximale sous la volonté disponible": patch_sheet(
            lea, sheet_id, "willpower_max", 3, 4
        ),
        "nom vide": patch_sheet(lea, sheet_id, "name", "  ", "Isaac Thorne"),
        "champ inconnu": patch_sheet(lea, sheet_id, "owner_id", "x", "y"),
        "type incohérent": patch_sheet(lea, sheet_id, "strength", "4", 2),
    }

    for label, response in refusals.items():
        assert response.status_code == 422, label
        assert error_code(response) == "rule_violation", label
    assert rule(refusals["attribut au-dessus de 5"]) == "range"
    assert rule(refusals["volonté au-dessus du maximum"]) == "willpower_above_max"
    assert rule(refusals["champ inconnu"]) == "unknown_field"


# --- Piste de blessures -------------------------------------------------------------


def _wound(actor: Actor, sheet_id: str, action: str, wound: str | None, expected: str) -> Response:
    return actor.request(
        "POST",
        f"/api/sheets/{sheet_id}/wounds",
        json={"action": action, "wound": wound, "expected": expected},
    )


def test_wounds_stay_ordered_and_within_health(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea, effective={"health_max": 3})["sheets"][0]["id"]

    assert _wound(lea, sheet_id, "add", "/", "").json()["sheets"][0]["wound_track"] == "/"
    assert _wound(lea, sheet_id, "add", "*", "/").json()["sheets"][0]["wound_track"] == "*/"
    assert _wound(lea, sheet_id, "add", "X", "*/").json()["sheets"][0]["wound_track"] == "*X/"

    full = _wound(lea, sheet_id, "add", "*", "*X/")
    assert full.status_code == 422
    assert rule(full) == "TrackFullError"

    assert _wound(lea, sheet_id, "worsen", "/", "*X/").json()["sheets"][0]["wound_track"] == "*XX"
    assert _wound(lea, sheet_id, "heal", None, "*XX").json()["sheets"][0]["wound_track"] == "*X"


def test_health_cannot_drop_below_the_wounds_taken(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    _wound(lea, sheet_id, "add", "X", "")
    _wound(lea, sheet_id, "add", "X", "X")

    response = patch_sheet(lea, sheet_id, "health_max", 1, 7)

    assert response.status_code == 422
    assert rule(response) == "health_below_wounds"


def test_wound_change_on_a_stale_track_is_a_conflict(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    _wound(lea, sheet_id, "add", "/", "")

    assert _wound(lea, sheet_id, "add", "/", "").status_code == 409


# --- Éveil : secret du MJ ----------------------------------


def test_nothing_about_the_awakening_reaches_the_player_before_it_happens(
    ctx: TestContext,
) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)

    for path in (f"/api/characters/{character['id']}", "/api/characters"):
        assert "awaken" not in lea.request("GET", path).text.lower()
    refused = patch_sheet(lea, character["sheets"][0]["id"], "strength", 6, 2)
    assert "awaken" not in refused.text.lower()
    assert "éveil" not in refused.text.lower()
    assert gm.request("GET", f"/api/characters/{character['id']}").json()["awakened_at"] is None


def test_awakening_raises_the_attribute_cap_to_ten_for_that_character(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character = create(lea)
    sheet_id = character["sheets"][0]["id"]

    ctx.characters.awaken(UUID(character["id"]))

    seen_by_player = lea.request("GET", f"/api/characters/{character['id']}").json()
    assert seen_by_player["awakened"] is True
    assert "awakened_at" not in seen_by_player
    assert gm.request("GET", f"/api/characters/{character['id']}").json()["awakened_at"]
    assert patch_sheet(lea, sheet_id, "strength", 8, 2).status_code == 200
    assert patch_sheet(lea, sheet_id, "strength", 11, 8).status_code == 422
    # Les compétences restent plafonnées à 5.
    assert patch_sheet(lea, sheet_id, "firearms", 6, 3).status_code == 422


# --- Avantage surnaturel -------------------------------------------------------


def test_supernatural_advantage_stays_between_one_and_ten(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]
    path = f"/api/characters/{character_id}"

    raised = lea.request(
        "PATCH", path, json={"field": "supernatural_level", "value": 4, "expected": 1}
    )
    named = lea.request(
        "PATCH", path, json={"field": "supernatural_name", "value": " Vigile ", "expected": ""}
    )
    emptied = lea.request(
        "PATCH", path, json={"field": "supernatural_level", "value": 0, "expected": 4}
    )

    assert raised.json()["supernatural_level"] == 4
    assert named.json()["supernatural_name"] == "Vigile"
    assert emptied.status_code == 422


# --- Formes du personnage --------------------------------------------------


def test_new_form_copies_the_main_one_and_lives_its_own_life(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)

    added = lea.request(
        "POST", f"/api/characters/{character['id']}/forms", json={"form_name": "Loup-garou"}
    ).json()
    main, form = added["sheets"]
    patch_sheet(lea, form["id"], "strength", 5, 2)
    renamed = patch_sheet(lea, form["id"], "form_name", "Bête", "Loup-garou").json()

    assert (form["is_main"], form["form_name"]) == (False, "Loup-garou")
    assert form["attributes"] == main["attributes"]
    assert form["specialties"] == main["specialties"]
    assert renamed["sheets"][0]["attributes"]["strength"] == 2
    assert renamed["sheets"][1]["attributes"]["strength"] == 5
    assert renamed["sheets"][1]["form_name"] == "Bête"


def test_main_form_cannot_be_deleted_but_another_can(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)
    added = lea.request(
        "POST", f"/api/characters/{character['id']}/forms", json={"form_name": "Double"}
    ).json()
    main_id, form_id = (sheet["id"] for sheet in added["sheets"])

    refused = lea.request("DELETE", f"/api/sheets/{main_id}")
    removed = lea.request("DELETE", f"/api/sheets/{form_id}")

    assert refused.status_code == 422
    assert rule(refused) == "main_form"
    assert [sheet["id"] for sheet in removed.json()["sheets"]] == [main_id]


# --- Suppression et personnage joué ------------------------------------------------


def test_owner_deletes_a_character_for_good(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    character_id = create(lea)["id"]

    by_gm = gm.request("DELETE", f"/api/characters/{character_id}")
    by_owner = lea.request("DELETE", f"/api/characters/{character_id}")

    assert by_gm.status_code == 403
    assert by_owner.status_code == 204
    assert lea.request("GET", f"/api/characters/{character_id}").status_code == 404
    assert lea.request("GET", "/api/characters").json()["characters"] == []


def test_last_created_character_is_played_until_the_player_picks_another(
    ctx: TestContext,
) -> None:
    lea = player(ctx, "lea.vale")
    first = create(lea)
    second = create(lea, identity={"name": "Nora Blackwood"})

    assert second["is_played"] is True
    chosen = lea.request("POST", f"/api/characters/{first['id']}/play").json()

    assert chosen["is_played"] is True
    played = {
        c["id"]: c["is_played"] for c in lea.request("GET", "/api/characters").json()["characters"]
    }
    assert played == {first["id"]: True, second["id"]: False}


def test_unknown_identifiers_are_not_found(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    assert lea.request("GET", f"/api/characters/{uuid4()}").status_code == 404
    assert patch_sheet(lea, str(uuid4()), "strength", 3, 2).status_code == 404
