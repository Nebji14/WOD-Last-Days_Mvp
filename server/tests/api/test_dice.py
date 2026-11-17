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

    response = _roll(lea, isaac, attribute="dexterity", second="firearms", specialty=True)

    assert response.status_code == 201, response.text
    roll = response.json()
    assert _parts(roll) == [("dexterity", 3), ("firearms", 3), ("specialty", 1)]
    assert roll["stages"] == [[8, 9, 2, 5, 1, 3, 4]]
    assert roll["successes"] == 2
    assert roll["outcome"] == "success"
    published = _messages(lea)[-1]
    assert published["roll"]["id"] == roll["id"]
    assert published["body"] == "Isaac Thorne · 2 réussites"


def test_tens_wait_for_the_roller_then_finish(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    isaac = create(lea)
    ctx.dice.faces = [10, 10, 3, 4, 2, 10, 6]

    first = _roll(lea, isaac, attribute="strength", second="athletics").json()
    assert first["stages"] == [[10, 10, 3, 4]]
    assert first["pending"] == 2
    assert first["outcome"] is None
    assert _messages(lea) == []

    second = lea.request("POST", f"/api/dice/rolls/{first['id']}/reroll").json()
    assert second["stages"][1] == [2, 10]
    assert second["pending"] == 1

    last = lea.request("POST", f"/api/dice/rolls/{first['id']}/reroll").json()
    assert last["pending"] == 0
    assert last["successes"] == 3
    assert _messages(lea)[-1]["roll"]["stages"] == [[10, 10, 3, 4], [2, 10], [6]]


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
