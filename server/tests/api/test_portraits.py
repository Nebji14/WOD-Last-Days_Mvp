"""Portraits : une image par forme, droits de lecture et suppression des fichiers."""

from typing import Any
from uuid import UUID

import pytest
from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.api.test_characters import create
from tests.api.test_npcs import new_npc
from tests.conftest import TestContext

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


def put_portrait(actor: Actor, sheet_id: str, content: bytes = PNG) -> Response:
    return actor.request("PUT", f"/api/sheets/{sheet_id}/portrait", content=content)


def portrait_of(response: Response, index: int = 0) -> str:
    assert response.status_code == 200, response.text
    return str(response.json()["sheets"][index]["portrait"])


def get_portrait(actor: Actor, name: str) -> Response:
    return actor.request("GET", f"/api/portraits/{name}")


def add_form(actor: Actor, character_id: str) -> dict[str, Any]:
    response = actor.request(
        "POST", f"/api/characters/{character_id}/forms", json={"form_name": "Loup-garou"}
    )
    character: dict[str, Any] = response.json()
    return character


# --- Une image par forme ----------------------------------------------------------------


def test_new_character_has_no_portrait(ctx: TestContext) -> None:
    assert create(player(ctx, "lea.vale"))["sheets"][0]["portrait"] is None


def test_each_form_keeps_its_own_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)
    main_id = character["sheets"][0]["id"]
    human = portrait_of(put_portrait(lea, main_id))

    with_wolf = add_form(lea, character["id"])
    wolf_id = with_wolf["sheets"][1]["id"]
    assert with_wolf["sheets"][1]["portrait"] is None

    wolf = portrait_of(put_portrait(lea, wolf_id, WEBP), index=1)

    sheets = lea.request("GET", f"/api/characters/{character['id']}").json()["sheets"]
    assert [sheet["portrait"] for sheet in sheets] == [human, wolf]
    assert get_portrait(lea, human).content == PNG
    assert get_portrait(lea, wolf).content == WEBP
    assert get_portrait(lea, wolf).headers["content-type"] == "image/webp"


def test_replacing_a_portrait_removes_the_former_file(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    former = portrait_of(put_portrait(lea, sheet_id))

    current = portrait_of(put_portrait(lea, sheet_id, WEBP))

    assert set(ctx.storage.files) == {current}
    assert get_portrait(lea, former).status_code == 404


def test_removing_a_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    put_portrait(lea, sheet_id)

    response = lea.request("DELETE", f"/api/sheets/{sheet_id}/portrait")

    assert response.json()["sheets"][0]["portrait"] is None
    assert ctx.storage.files == {}


def test_deleting_a_form_removes_only_its_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)
    human = portrait_of(put_portrait(lea, character["sheets"][0]["id"]))
    wolf_id = add_form(lea, character["id"])["sheets"][1]["id"]
    put_portrait(lea, wolf_id)

    lea.request("DELETE", f"/api/sheets/{wolf_id}")

    assert set(ctx.storage.files) == {human}


def test_deleting_a_character_removes_every_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)
    put_portrait(lea, character["sheets"][0]["id"])
    put_portrait(lea, add_form(lea, character["id"])["sheets"][1]["id"])

    lea.request("DELETE", f"/api/characters/{character['id']}")

    assert ctx.storage.files == {}


# --- Photo entière, gardée pour recadrer -------------------------------------------------


def put_original(actor: Actor, name: str, content: bytes = WEBP) -> Response:
    return actor.request("PUT", f"/api/portraits/{name}/original", content=content)


def get_original(actor: Actor, name: str) -> Response:
    return actor.request("GET", f"/api/portraits/{name}/original")


def test_original_is_kept_and_read_again(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))
    assert get_original(lea, name).status_code == 404

    assert put_original(lea, name, PNG).status_code == 204
    assert put_original(lea, name, WEBP).status_code == 204

    assert get_original(lea, name).content == WEBP
    assert get_portrait(lea, name).content == PNG


def test_original_is_reserved_to_those_who_edit_the_sheet(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))
    put_original(lea, name)

    # Le portrait est visible sur le siège, pas la photo entière.
    assert get_portrait(ben, name).status_code == 200
    assert get_original(ben, name).status_code == 404
    assert put_original(ben, name, PNG).status_code == 404
    assert get_original(gm, name).content == WEBP


def test_original_leaves_with_its_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    put_original(lea, portrait_of(put_portrait(lea, sheet_id)))
    assert len(ctx.storage.files) == 2

    current = portrait_of(put_portrait(lea, sheet_id, WEBP))
    assert set(ctx.storage.files) == {current}

    put_original(lea, current)
    lea.request("DELETE", f"/api/sheets/{sheet_id}/portrait")
    assert ctx.storage.files == {}


def test_invalid_original_is_refused(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))

    assert error_code(put_original(lea, name, b"<svg></svg>")) == "unsupported_image"
    too_large = PNG + b"\x00" * (4 * 1024 * 1024)
    assert error_code(put_original(lea, name, too_large)) == "image_too_large"


# --- Contrôle du fichier ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"<svg></svg>", "unsupported_image"),
        (b"", "image_too_large"),
        (PNG + b"\x00" * (2 * 1024 * 1024), "image_too_large"),
    ],
)
def test_invalid_file_is_refused(ctx: TestContext, content: bytes, code: str) -> None:
    lea = player(ctx, "lea.vale")

    response = put_portrait(lea, create(lea)["sheets"][0]["id"], content)

    assert error_code(response) == code
    assert ctx.storage.files == {}


def test_storage_failure_keeps_the_former_portrait(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    character = create(lea)
    former = portrait_of(put_portrait(lea, character["sheets"][0]["id"]))
    ctx.storage.available = False

    response = put_portrait(lea, character["sheets"][0]["id"], WEBP)

    assert response.status_code == 503
    sheets = lea.request("GET", f"/api/characters/{character['id']}").json()["sheets"]
    assert sheets[0]["portrait"] == former


def test_database_failure_leaves_no_orphan_file(
    ctx: TestContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]

    async def fail(sheet_id: UUID, path: str | None) -> None:
        raise RuntimeError("base indisponible")

    monkeypatch.setattr(ctx.characters, "set_portrait", fail)
    with pytest.raises(RuntimeError, match="base indisponible"):
        put_portrait(lea, sheet_id)

    assert ctx.storage.files == {}


@pytest.mark.parametrize("name", ["x.png", "../secret", "a" * 32 + ".svg"])
def test_unexpected_portrait_name_is_refused(ctx: TestContext, name: str) -> None:
    lea = player(ctx, "lea.vale")

    assert get_portrait(lea, name).status_code in (404, 422)


# --- Droits -----------------------------------------------------------------------------


def test_portrait_requires_a_session(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))

    assert ctx.client.get(f"/api/portraits/{name}").status_code == 401


def test_played_main_form_is_seen_by_everyone(ctx: TestContext) -> None:
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))

    assert get_portrait(ben, name).status_code == 200


def test_other_forms_stay_secret_for_other_players(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    wolf_id = add_form(lea, create(lea)["id"])["sheets"][1]["id"]
    wolf = portrait_of(put_portrait(lea, wolf_id), index=1)

    assert get_portrait(ben, wolf).status_code == 404
    assert get_portrait(gm, wolf).status_code == 200


def test_character_not_played_stays_secret_for_other_players(ctx: TestContext) -> None:
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    name = portrait_of(put_portrait(lea, create(lea)["sheets"][0]["id"]))
    create(lea)

    assert get_portrait(ben, name).status_code == 404


def test_another_player_cannot_change_a_portrait(ctx: TestContext) -> None:
    lea, ben = player(ctx, "lea.vale"), player(ctx, "ben")
    sheet_id = create(lea)["sheets"][0]["id"]
    put_portrait(lea, sheet_id)

    assert put_portrait(ben, sheet_id).status_code == 404
    assert ben.request("DELETE", f"/api/sheets/{sheet_id}/portrait").status_code == 404
    assert len(ctx.storage.files) == 1


def test_gm_changes_the_portrait_of_a_player(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")

    assert put_portrait(gm, create(lea)["sheets"][0]["id"]).status_code == 200


def test_npc_portrait_is_reserved_to_the_gm_and_removed_with_it(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    npc = new_npc(gm)
    name = portrait_of(put_portrait(gm, npc["sheets"][0]["id"]))

    assert get_portrait(lea, name).status_code == 404
    assert get_portrait(gm, name).status_code == 200

    gm.request("DELETE", f"/api/npcs/{npc['id']}")
    assert ctx.storage.files == {}


def test_npc_portrait_is_listed_in_the_gm_tool(ctx: TestContext) -> None:
    gm = game_master(ctx)
    npc = new_npc(gm)
    sheet_id = npc["sheets"][0]["id"]

    name = portrait_of(put_portrait(gm, sheet_id))

    [card] = gm.request("GET", "/api/npcs").json()["npcs"]
    assert (card["sheet_id"], card["portrait"]) == (sheet_id, name)


# --- Photo du MJ ------------------------------------------------------------------------


def put_gm_portrait(actor: Actor, content: bytes = PNG) -> Response:
    return actor.request("PUT", "/api/account/portrait", content=content)


def test_gm_photo_is_seen_by_everyone_and_replaced(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    former = put_gm_portrait(gm).json()["portrait"]
    assert get_portrait(lea, former).content == PNG

    current = put_gm_portrait(gm, WEBP).json()["portrait"]

    assert gm.request("GET", "/api/auth/me").json()["portrait"] == current
    assert get_portrait(lea, current).content == WEBP
    assert set(ctx.storage.files) == {current}


def test_gm_photo_is_removed(ctx: TestContext) -> None:
    gm = game_master(ctx)
    name = put_gm_portrait(gm).json()["portrait"]
    put_original(gm, name)

    response = gm.request("DELETE", "/api/account/portrait")

    assert response.json()["portrait"] is None
    assert ctx.storage.files == {}


def test_gm_original_stays_private(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    name = put_gm_portrait(gm).json()["portrait"]
    put_original(gm, name)

    assert get_original(gm, name).status_code == 200
    assert get_original(lea, name).status_code == 404


def test_account_photo_is_reserved_to_the_gm(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")

    assert put_gm_portrait(lea).status_code == 403
    assert lea.request("DELETE", "/api/account/portrait").status_code == 403
    assert ctx.client.put("/api/account/portrait", content=PNG).status_code == 401


def test_invalid_gm_photo_is_refused(ctx: TestContext) -> None:
    gm = game_master(ctx)

    assert error_code(put_gm_portrait(gm, b"<svg></svg>")) == "unsupported_image"
    assert ctx.storage.files == {}


def test_gm_photo_reaches_the_table(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    with ctx.client.websocket_connect("/ws") as session:
        session.send_json({"type": "auth", "ticket": lea.ticket()})
        assert session.receive_json()["data"]["gm"]["portrait"] is None

        name = put_gm_portrait(gm).json()["portrait"]

        session.receive_json()
        state = session.receive_json()

    assert state["data"]["gm"]["portrait"] == name


# --- Temps réel -------------------------------------------------------------------------


def test_new_portrait_reaches_the_seat(ctx: TestContext) -> None:
    lea = player(ctx, "lea.vale")
    sheet_id = create(lea)["sheets"][0]["id"]
    with ctx.client.websocket_connect("/ws") as session:
        session.send_json({"type": "auth", "ticket": lea.ticket()})
        session.receive_json()

        name = portrait_of(put_portrait(lea, sheet_id))

        changed, state = session.receive_json(), session.receive_json()

    assert changed["type"] == "character.changed"
    assert state["data"]["seats"][0]["character"]["portrait"] == name
