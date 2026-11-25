"""Musique : droits, diffusion à la table, file d'attente et playlists."""

from typing import Any
from uuid import uuid4

import pytest
from httpx import Response

from app.gateways.youtube import MusicQuotaError
from tests.api.helpers import Actor, error_code, game_master, player
from tests.conftest import TestContext
from tests.fake_music import DAWN, DOCKS, HUNT


def play(gm: Actor, video_id: str = HUNT.video_id) -> Response:
    return gm.request("POST", "/api/music/play", json={"video_id": video_id})


def enqueue(gm: Actor, video_id: str) -> Response:
    return gm.request("POST", "/api/music/queue", json={"video_id": video_id})


def now(actor: Actor) -> dict[str, Any]:
    data: dict[str, Any] = actor.request("GET", "/api/music").json()
    return data


def deck(gm: Actor) -> dict[str, Any]:
    data: dict[str, Any] = gm.request("GET", "/api/music/deck").json()
    return data


def playlists(gm: Actor) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = gm.request("GET", "/api/playlists").json()["playlists"]
    return data


def playlist(gm: Actor, *video_ids: str, name: str = "Combat") -> str:
    playlist_id = str(gm.request("POST", "/api/playlists", json={"name": name}).json()["id"])
    for video_id in video_ids:
        path = f"/api/playlists/{playlist_id}/tracks"
        assert gm.request("POST", path, json={"video_id": video_id}).status_code == 204
    return playlist_id


# --- Droits --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/music/deck", None),
        ("GET", "/api/music/search?q=docks", None),
        ("GET", "/api/music/suggestions?q=hans", None),
        ("POST", "/api/music/play", {"video_id": HUNT.video_id}),
        ("POST", "/api/music/pause", None),
        ("POST", "/api/music/resume", None),
        ("POST", "/api/music/stop", None),
        ("POST", "/api/music/skip", {"play_id": 1}),
        ("PUT", "/api/music/position", {"seconds": 1}),
        ("PUT", "/api/music/repeat", {"mode": "track"}),
        ("PUT", "/api/music/video", {"shown": True}),
        ("POST", "/api/music/queue", {"video_id": HUNT.video_id}),
        ("DELETE", "/api/music/queue", None),
        ("POST", f"/api/music/queue/{uuid4()}/play", None),
        ("PUT", f"/api/music/queue/{uuid4()}/index", {"index": 0}),
        ("DELETE", f"/api/music/queue/{uuid4()}", None),
        ("GET", "/api/playlists", None),
        ("POST", "/api/playlists", {"name": "Combat"}),
        ("PATCH", f"/api/playlists/{uuid4()}", {"name": "Combat"}),
        ("DELETE", f"/api/playlists/{uuid4()}", None),
        ("POST", f"/api/playlists/{uuid4()}/tracks", {"video_id": HUNT.video_id}),
        ("DELETE", f"/api/playlists/{uuid4()}/tracks/{uuid4()}", None),
        ("POST", f"/api/playlists/{uuid4()}/play", {}),
    ],
)
def test_commands_are_reserved_to_the_gm(
    ctx: TestContext, method: str, path: str, body: dict[str, Any] | None
) -> None:
    lea = player(ctx, "lea.vale")

    assert lea.request(method, path, json=body).status_code == 403
    assert ctx.client.request(method, path, json=body).status_code == 401


def test_listening_requires_a_session(ctx: TestContext) -> None:
    assert ctx.client.get("/api/music").status_code == 401


# --- Recherche -----------------------------------------------------------------------------


def test_search_by_text_and_by_link(ctx: TestContext) -> None:
    gm = game_master(ctx)

    by_text = gm.request("GET", "/api/music/search", params={"q": "docks"}).json()["tracks"]
    link = f"https://youtu.be/{DAWN.video_id}"
    by_link = gm.request("GET", "/api/music/search", params={"q": link}).json()["tracks"]

    assert [track["video_id"] for track in by_text] == [DOCKS.video_id]
    assert [track["title"] for track in by_link] == [DAWN.title]
    assert ctx.music.searches == ["docks"]


def test_suggestions_use_no_search(ctx: TestContext) -> None:
    gm = game_master(ctx)

    response = gm.request("GET", "/api/music/suggestions", params={"q": "hans zim"})
    too_short = gm.request("GET", "/api/music/suggestions", params={"q": "ha"})

    assert response.json() == {"suggestions": ["Hans Zimmer - Time"]}
    assert too_short.status_code == 422
    assert ctx.music.searches == []


def test_an_exhausted_quota_is_explained(ctx: TestContext) -> None:
    gm = game_master(ctx)
    ctx.music.error = MusicQuotaError()

    response = gm.request("GET", "/api/music/search", params={"q": "docks"})

    assert response.status_code == 503
    assert error_code(response) == "music_quota_reached"


def test_an_unknown_track_is_refused(ctx: TestContext) -> None:
    gm = game_master(ctx)

    assert error_code(play(gm, "inconnu0000")) == "track_unavailable"
    assert play(gm, "../../etc").status_code == 422
    assert now(gm)["track"] is None


# --- Diffusion -----------------------------------------------------------------------------


def test_a_player_joining_late_hears_the_current_position(ctx: TestContext) -> None:
    gm = game_master(ctx)
    assert play(gm).status_code == 204
    ctx.clock.advance(42.0)

    heard = now(player(ctx, "lea.vale"))

    assert heard["track"]["video_id"] == HUNT.video_id
    assert heard["playing"] is True
    assert heard["position"] == 42.0
    assert "queue" not in heard


def test_everyone_is_told_without_the_queue(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    with ctx.client.websocket_connect("/ws") as session:
        session.send_json({"type": "auth", "ticket": lea.ticket()})
        assert session.receive_json()["type"] == "table.state"
        play(gm)
        event = session.receive_json()

    assert event["type"] == "music.changed"
    assert event["data"]["track"]["title"] == HUNT.title
    assert set(event["data"]) == {"play_id", "track", "playing", "position", "video_shown"}


def test_pause_resume_seek_and_stop(ctx: TestContext) -> None:
    gm = game_master(ctx)
    play(gm)
    ctx.clock.advance(10.0)
    gm.request("POST", "/api/music/pause")
    ctx.clock.advance(100.0)
    assert (now(gm)["playing"], now(gm)["position"]) == (False, 10.0)

    gm.request("PUT", "/api/music/position", json={"seconds": 60})
    gm.request("POST", "/api/music/resume")
    ctx.clock.advance(5.0)
    assert (now(gm)["playing"], now(gm)["position"]) == (True, 65.0)

    gm.request("POST", "/api/music/stop")
    assert now(gm)["track"] is None


def test_the_gm_shows_and_hides_the_video_for_everyone(ctx: TestContext) -> None:
    gm = game_master(ctx)
    lea = player(ctx, "lea.vale")
    play(gm)
    assert now(lea)["video_shown"] is False

    gm.request("PUT", "/api/music/video", json={"shown": True})
    assert now(lea)["video_shown"] is True
    gm.request("PUT", "/api/music/video", json={"shown": False})
    assert now(lea)["video_shown"] is False

    body = {"video_id": DOCKS.video_id, "show_video": True}
    gm.request("POST", "/api/music/play", json=body)
    assert now(lea)["video_shown"] is True


def test_skip_ignores_an_outdated_request(ctx: TestContext) -> None:
    gm = game_master(ctx)
    play(gm)
    enqueue(gm, DOCKS.video_id)
    enqueue(gm, DAWN.video_id)
    play_id = now(gm)["play_id"]

    for _ in range(2):
        gm.request("POST", "/api/music/skip", json={"play_id": play_id})

    assert now(gm)["track"]["video_id"] == DOCKS.video_id


def test_repeat_mode_is_kept(ctx: TestContext) -> None:
    gm = game_master(ctx)

    assert gm.request("PUT", "/api/music/repeat", json={"mode": "queue"}).status_code == 204
    assert gm.request("PUT", "/api/music/repeat", json={"mode": "x"}).status_code == 422
    assert deck(gm)["repeat"] == "queue"


# --- File d'attente --------------------------------------------------------------------------


def test_queue_moves_plays_removes_and_clears(ctx: TestContext) -> None:
    gm = game_master(ctx)
    play(gm)
    for track in (DOCKS, DAWN, HUNT):
        enqueue(gm, track.video_id)
    docks, dawn, hunt = (item["id"] for item in deck(gm)["queue"])

    gm.request("PUT", f"/api/music/queue/{hunt}/index", json={"index": 0})
    assert [item["id"] for item in deck(gm)["queue"]] == [hunt, docks, dawn]

    gm.request("POST", f"/api/music/queue/{dawn}/play")
    assert now(gm)["track"]["video_id"] == DAWN.video_id

    gm.request("DELETE", f"/api/music/queue/{docks}")
    assert [item["id"] for item in deck(gm)["queue"]] == [hunt]
    assert gm.request("DELETE", f"/api/music/queue/{docks}").status_code == 404

    gm.request("DELETE", "/api/music/queue")
    assert deck(gm)["queue"] == []
    assert now(gm)["track"]["video_id"] == DAWN.video_id


# --- Playlists -------------------------------------------------------------------------------


def test_playlist_lifecycle(ctx: TestContext) -> None:
    gm = game_master(ctx)
    playlist_id = playlist(gm, HUNT.video_id, DOCKS.video_id)

    renamed = gm.request("PATCH", f"/api/playlists/{playlist_id}", json={"name": "  Traque "})
    assert renamed.status_code == 204
    [found] = playlists(gm)
    assert found["name"] == "Traque"
    assert [entry["track"]["video_id"] for entry in found["tracks"]] == [
        HUNT.video_id,
        DOCKS.video_id,
    ]

    entry_id = found["tracks"][0]["id"]
    gm.request("DELETE", f"/api/playlists/{playlist_id}/tracks/{entry_id}")
    assert len(playlists(gm)[0]["tracks"]) == 1

    gm.request("DELETE", f"/api/playlists/{playlist_id}")
    assert playlists(gm) == []


def test_playing_a_playlist_replaces_the_queue(ctx: TestContext) -> None:
    gm = game_master(ctx)
    play(gm, DAWN.video_id)
    enqueue(gm, DAWN.video_id)
    playlist_id = playlist(gm, HUNT.video_id, DOCKS.video_id)

    gm.request("POST", f"/api/playlists/{playlist_id}/play", json={})
    assert now(gm)["track"]["video_id"] == HUNT.video_id
    assert [i["track"]["video_id"] for i in deck(gm)["queue"]] == [DOCKS.video_id]

    gm.request("POST", f"/api/playlists/{playlist_id}/play", json={"shuffled": True})
    assert now(gm)["track"]["video_id"] == DOCKS.video_id


def test_playlist_refusals(ctx: TestContext) -> None:
    gm = game_master(ctx)
    empty = playlist(gm)

    assert error_code(gm.request("POST", f"/api/playlists/{empty}/play", json={})) == (
        "playlist_empty"
    )
    assert gm.request("POST", "/api/playlists", json={"name": "   "}).status_code == 422
    missing = f"/api/playlists/{uuid4()}"
    assert gm.request("PATCH", missing, json={"name": "x"}).status_code == 404
    assert gm.request("DELETE", missing).status_code == 404
    assert gm.request("POST", f"{missing}/play", json={}).status_code == 404
