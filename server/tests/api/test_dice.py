"""Jets de dés : composition depuis la fiche, relances, volonté, chat et droits."""

from typing import Any

from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.api.test_characters import create
from tests.conftest import TestContext


def _roll(actor: Actor, character: dict[str, Any] | None = None, **fields: Any) -> Response:
    payload: dict[str, Any] = {"kind": "pool"} | fields
    if character is not None:
        payload |= {"character_id": character["id"], "sheet_id": character["sheets"][0]["id"]}
    return actor.request("POST", "/api/dice/rolls", json=payload)


def _messages(actor: Actor) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = actor.request("GET", "/api/chat/messages").json()["messages"]
    return messages


def _parts(roll: dict[str, Any]) -> list[tuple[str, int]]:
    return [(part["key"], part["value"]) for part in roll["parts"]]


def test_roll_is_built_from_the_sheet_and_published_in_chat(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    ctx.dice.faces = [8, 9, 2, 5, 1, 3, 4]

    response = _roll(lea, isaac, attribute="dexterity", second="firearms")

    assert response.status_code == 201, response.text
    roll = response.json()
    assert _parts(roll) == [("dexterity", 3), ("firearms", 3)]
    assert roll["stages"] == [[8, 9, 2, 5, 1, 3]]
    assert roll["successes"] == 2
    assert roll["outcome"] == "success"
    published = _messages(lea)[-1]
    assert published["roll"]["id"] == roll["id"]
    assert published["body"] == "Isaac Thorne · 2 réussites"


def test_tens_are_rerolled_once_only(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    ctx.dice.faces = [10, 10, 3, 4, 2, 10]

    first = _roll(lea, isaac, attribute="strength", second="athletics").json()
    assert first["stages"] == [[10, 10, 3, 4]]
    assert first["pending"] == 2
    assert first["outcome"] is None
    assert _messages(lea) == []

    last = lea.request("POST", f"/api/dice/rolls/{first['id']}/reroll").json()
    assert last["stages"][1] == [2, 10]
    assert last["pending"] == 0  # le nouveau 10 ne se relance pas
    assert last["successes"] == 3
    assert _messages(lea)[-1]["roll"]["stages"] == [[10, 10, 3, 4], [2, 10]]

    again = lea.request("POST", f"/api/dice/rolls/{first['id']}/reroll")
    assert again.status_code == 404


def test_specialty_counts_tens_twice_instead_of_rerolling(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    ctx.dice.faces = [10, 10, 9, 3]

    roll = _roll(lea, isaac, attribute="strength", second="athletics", specialty=True).json()

    assert _parts(roll) == [("strength", 2), ("athletics", 2)]
    assert roll["pending"] == 0
    assert roll["specialty"] is True
    assert roll["doubled"] == 2
    assert roll["successes"] == 5
    assert roll["outcome"] == "exceptional"
    assert _messages(lea)[-1]["body"] == "Isaac Thorne · 5 réussites (2 dés comptés double)"


def test_specialty_needs_no_specialty_written_on_the_skill(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ctx.dice.faces = [9, 9, 1, 1]

    roll = _roll(
        lea, create(lea), attribute="strength", second="stealth", specialty=True, again=9
    ).json()

    assert roll["doubled"] == 2
    assert roll["successes"] == 4


def test_specialty_is_refused_on_initiative(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    response = _roll(lea, create(lea), kind="initiative", specialty=True)

    assert response.status_code == 422


def test_only_the_roller_rerolls(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    gm = game_master(ctx)
    ctx.dice.faces = [10, 3, 3, 3]
    roll = _roll(lea, create(lea), attribute="strength", second="athletics").json()

    response = gm.request("POST", f"/api/dice/rolls/{roll['id']}/reroll")

    assert response.status_code == 403


def test_willpower_adds_three_dice_and_costs_one_point(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    before = isaac["sheets"][0]["willpower_current"]

    roll = _roll(lea, isaac, attribute="wits", second="investigation", willpower=True).json()

    assert ("willpower", 3) in _parts(roll)
    sheet = lea.request("GET", f"/api/characters/{isaac['id']}").json()["sheets"][0]
    assert sheet["willpower_current"] == before - 1


def test_empty_pool_rolls_a_chance_die(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ctx.dice.faces = [1]

    roll = _roll(lea, create(lea), attribute="wits", second="computer", modifier=-5).json()

    assert roll["chance"] is True
    assert roll["stages"] == [[1]]
    assert roll["outcome"] == "dramatic_failure"


def test_initiative_adds_one_die(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    ctx.dice.faces = [7]

    roll = _roll(lea, create(lea), kind="initiative").json()

    assert roll["total"] == 5 + 7
    assert _messages(lea)[-1]["body"] == "Isaac Thorne · initiative 12"


def test_player_cannot_roll_for_someone_else(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    tom = player(ctx, "tom")

    response = _roll(tom, create(lea), attribute="strength", second="brawl")

    assert response.status_code == 404


def test_secret_and_free_rolls_belong_to_the_gm(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    gm = game_master(ctx)

    refused = _roll(lea, kind="free", dice=3, secret=True)
    secret = _roll(gm, kind="free", dice=3, secret=True)

    assert refused.status_code == 403
    assert error_code(refused) == "forbidden"
    assert secret.status_code == 201
    assert _messages(gm) == []


def test_roll_message_cannot_be_edited(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    _roll(lea, create(lea), attribute="strength", second="brawl")
    message = _messages(lea)[-1]

    response = lea.request("PATCH", f"/api/chat/messages/{message['id']}", json={"body": "triche"})

    assert response.status_code == 403


# --- Pouvoirs, armes et atouts : recette de jet -----------------------------------------


def _power(actor: Actor, character: dict[str, Any], **recipe: Any) -> dict[str, Any]:
    """Ajoute un pouvoir avec sa recette et retourne l'élément créé."""
    sheet_id = character["sheets"][0]["id"]
    payload = {"kind": "power", "name": "Pensées et sentiments", "level": 2, "roll": recipe}
    sheet = actor.request("POST", f"/api/sheets/{sheet_id}/entries", json=payload).json()
    entry: dict[str, Any] = sheet["sheets"][0]["entries"][-1]
    return entry


def test_power_rolls_its_recipe_and_costs_willpower(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    power = _power(lea, isaac, parts=["wits", "empathy"], willpower_cost=1)
    before = isaac["sheets"][0]["willpower_current"]

    roll = _roll(lea, isaac, kind="entry", entry_id=power["id"], modifier=-3).json()

    assert roll["label"] == "Pensées et sentiments"
    assert _parts(roll) == [("wits", 3), ("empathy", 2), ("supernatural", 1), ("modifier", -3)]
    sheet = lea.request("GET", f"/api/characters/{isaac['id']}").json()["sheets"][0]
    assert sheet["willpower_current"] == before - 1
    assert _messages(lea)[-1]["body"].startswith("Isaac Thorne · Pensées et sentiments · ")


def test_power_can_be_rolled_under_specialty(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    power = _power(lea, isaac, parts=["wits", "empathy"])
    ctx.dice.faces = [10, 2, 2, 2, 2, 2]

    roll = _roll(lea, isaac, kind="entry", entry_id=power["id"], specialty=True).json()

    assert roll["pending"] == 0
    assert roll["doubled"] == 1
    assert roll["successes"] == 2


def test_recipe_may_hold_more_than_two_traits(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    parts = ["presence", "empathy", "occult", "entry_level"]
    power = _power(lea, isaac, parts=parts)

    roll = _roll(lea, isaac, kind="entry", entry_id=power["id"]).json()

    assert [key for key, _ in _parts(roll)] == [*parts, "supernatural"]


def test_supernatural_advantage_is_added_once_and_never_stored(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    power = _power(lea, isaac, parts=["wits", "supernatural"])

    roll = _roll(lea, isaac, kind="entry", entry_id=power["id"]).json()

    assert power["roll"]["parts"] == ["wits"]
    assert [key for key, _ in _parts(roll)] == ["wits", "supernatural"]


def test_recipe_with_unknown_trait_is_refused(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    payload = {"kind": "power", "name": "X", "roll": {"parts": ["telepathy"]}}

    response = lea.request("POST", f"/api/sheets/{sheet_id}/entries", json=payload)

    assert response.status_code == 422


def test_power_cost_needs_enough_willpower(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    power = _power(lea, isaac, parts=["wits", "empathy"], willpower_cost=5)

    response = _roll(lea, isaac, kind="entry", entry_id=power["id"])

    assert response.status_code == 422


def test_gm_malus_and_bonus_both_count(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    roll = _roll(
        lea, create(lea), attribute="strength", second="athletics", modifier=-4, gm_bonus=2
    ).json()

    assert _parts(roll)[-2:] == [("modifier", -4), ("gm_bonus", 2)]
