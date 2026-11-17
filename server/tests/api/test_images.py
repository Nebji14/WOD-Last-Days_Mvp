"""Images : bibliothèque du MJ et images montrées à la table."""

from typing import Any

from httpx import Response

from tests.api.helpers import Actor, error_code, game_master, player
from tests.conftest import TestContext

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def upload(gm: Actor, filename: str = "Quai de nuit.png", **params: Any) -> Response:
    return gm.request("POST", "/api/images", params={"filename": filename, **params}, content=PNG)


def uploaded(gm: Actor, filename: str = "Quai de nuit.png", **params: Any) -> dict[str, Any]:
    response = upload(gm, filename, **params)
    assert response.status_code == 201, response.text
    image: dict[str, Any] = response.json()
    return image


def library(gm: Actor) -> dict[str, Any]:
    data: dict[str, Any] = gm.request("GET", "/api/images").json()
    return data


def scene(actor: Actor) -> dict[str, Any]:
    data: dict[str, Any] = actor.request("GET", "/api/table/images").json()
    return data


# --- Bibliothèque ------------------------------------------------------------------------


def test_upload_keeps_the_file_name_and_regenerates_the_stored_name(ctx: TestContext) -> None:
    gm = game_master(ctx)

    image = uploaded(gm)

    assert image["name"] == "Quai de nuit"
    [stored] = ctx.storage.files
    assert "Quai" not in stored
    assert stored.endswith(".png")
    assert library(gm)["images"][0]["url"].startswith("https://storage.test/")


def test_upload_refuses_a_file_that_is_not_an_image(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request(
        "POST", "/api/images", params={"filename": "photo.png"}, content=b"<svg></svg>"
    )

    assert response.status_code == 415
    assert error_code(response) == "unsupported_image"
    assert ctx.storage.files == {}


def test_upload_refuses_a_file_that_is_too_heavy(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request(
        "POST",
        "/api/images",
        params={"filename": "big.png"},
        content=PNG + b"\x00" * (8 * 1024 * 1024),
    )

    assert response.status_code == 413
    assert error_code(response) == "image_too_large"


def test_library_and_table_actions_are_reserved_to_the_gm(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    image_id = uploaded(gm)["id"]

    for method, path in (
        ("GET", "/api/images"),
        ("POST", f"/api/table/images/{image_id}/show"),
        ("DELETE", f"/api/images/{image_id}"),
        ("POST", "/api/image-folders"),
    ):
        assert lea.request(method, path, json={"name": "x"}).status_code == 403


def test_rename_and_move_an_image(ctx: TestContext) -> None:
    gm = game_master(ctx)
    image_id = uploaded(gm)["id"]
    folder_id = gm.request("POST", "/api/image-folders", json={"name": "Les docks"}).json()["id"]

    assert (
        gm.request("PATCH", f"/api/images/{image_id}", json={"name": " Quai "}).status_code == 204
    )
    moved = gm.request("PUT", f"/api/images/{image_id}/folder", json={"folder_id": folder_id})

    assert moved.status_code == 204
    [image] = library(gm)["images"]
    assert (image["name"], image["folder_id"]) == ("Quai", folder_id)


def test_deleting_a_folder_moves_its_content_to_the_parent(ctx: TestContext) -> None:
    gm = game_master(ctx)
    docks = gm.request("POST", "/api/image-folders", json={"name": "Les docks"}).json()["id"]
    places = gm.request(
        "POST", "/api/image-folders", json={"name": "Lieux", "parent_id": docks}
    ).json()["id"]
    image_id = uploaded(gm, folder_id=places)["id"]

    assert gm.request("DELETE", f"/api/image-folders/{places}").status_code == 204

    data = library(gm)
    assert [f["id"] for f in data["folders"]] == [docks]
    assert data["images"][0]["id"] == image_id
    assert data["images"][0]["folder_id"] == docks


def test_a_folder_cannot_be_moved_into_its_own_subfolder(ctx: TestContext) -> None:
    gm = game_master(ctx)
    docks = gm.request("POST", "/api/image-folders", json={"name": "Les docks"}).json()["id"]
    places = gm.request(
        "POST", "/api/image-folders", json={"name": "Lieux", "parent_id": docks}
    ).json()["id"]

    response = gm.request("PUT", f"/api/image-folders/{docks}/parent", json={"parent_id": places})

    assert response.status_code == 422
    assert error_code(response) == "folder_cycle"


# --- Table ---------------------------------------------------------------------------------


def test_shown_image_is_seen_by_players_then_put_down_on_the_pile(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    image_id = uploaded(gm)["id"]

    gm.request("POST", f"/api/table/images/{image_id}/show")
    paused = scene(lea)
    gm.request("POST", "/api/table/images/put-down")
    resumed = scene(lea)

    assert paused["shown"]["id"] == image_id
    assert paused["shown"]["url"]
    assert resumed["shown"] is None
    assert [i["id"] for i in resumed["pile"]] == [image_id]


def test_showing_a_new_image_puts_the_previous_one_on_the_pile(ctx: TestContext) -> None:
    gm = game_master(ctx)
    first = uploaded(gm, "a.png")["id"]
    second = uploaded(gm, "b.png")["id"]

    gm.request("POST", f"/api/table/images/{first}/show")
    gm.request("POST", f"/api/table/images/{second}/show")

    data = scene(gm)
    assert data["shown"]["id"] == second
    assert [i["id"] for i in data["pile"]] == [first]


def test_removing_from_the_table_keeps_the_image_in_the_library(ctx: TestContext) -> None:
    gm = game_master(ctx)
    image_id = uploaded(gm)["id"]
    gm.request("POST", f"/api/table/images/{image_id}/show")
    gm.request("POST", "/api/table/images/put-down")

    assert gm.request("DELETE", f"/api/table/images/{image_id}").status_code == 204

    assert scene(gm)["pile"] == []
    assert [i["id"] for i in library(gm)["images"]] == [image_id]


def test_deleting_an_image_on_the_table_removes_it_everywhere(ctx: TestContext) -> None:
    gm = game_master(ctx)
    image_id = uploaded(gm)["id"]
    gm.request("POST", f"/api/table/images/{image_id}/show")
    gm.request("POST", "/api/table/images/put-down")

    assert gm.request("DELETE", f"/api/images/{image_id}").status_code == 204

    assert scene(gm)["pile"] == []
    assert ctx.storage.files == {}


def test_scene_reports_storage_outage_generically(ctx: TestContext) -> None:
    gm = game_master(ctx)
    image_id = uploaded(gm)["id"]
    gm.request("POST", f"/api/table/images/{image_id}/show")
    ctx.storage.available = False

    response = gm.request("GET", "/api/table/images")

    assert response.status_code == 503
    assert error_code(response) == "service_unavailable"
