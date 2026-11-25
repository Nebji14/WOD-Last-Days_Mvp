"""Client de l'API YouTube : tri des vidéos, clé et refus."""

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.domain.music import Track
from app.gateways.youtube import (
    MusicNotConfiguredError,
    MusicQuotaError,
    MusicSourceError,
    YouTubeGateway,
)

KEY = "cle-de-test"
Handler = Callable[[httpx.Request], httpx.Response]


def video(video_id: str, duration: str = "PT3M", embeddable: bool = True) -> dict[str, Any]:
    return {
        "id": video_id,
        "snippet": {"title": f"Titre {video_id}", "channelTitle": "Chaîne"},
        "contentDetails": {"duration": duration},
        "status": {"embeddable": embeddable},
    }


def search(settings: Settings, handler: Handler, key: str = KEY) -> list[Track]:
    configured = settings.model_copy(update={"youtube_api_key": SecretStr(key)})

    async def run() -> list[Track]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await YouTubeGateway(configured, client).search("combat")

    return asyncio.run(run())


def test_only_playable_videos_are_kept_in_order(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            ids = ["aaaaaaaaaaa", "bbbbbbbbbbb", "ccccccccccc", "ddddddddddd"]
            return httpx.Response(200, json={"items": [{"id": {"videoId": i}} for i in ids]})
        items = [
            video("ddddddddddd"),
            video("bbbbbbbbbbb", embeddable=False),
            video("ccccccccccc", duration="P0D"),
            video("aaaaaaaaaaa"),
        ]
        return httpx.Response(200, json={"items": items})

    tracks = search(settings, handler)

    assert [track.video_id for track in tracks] == ["aaaaaaaaaaa", "ddddddddddd"]
    assert tracks[0].duration_seconds == 180


def test_the_key_never_appears_in_the_address(settings: Settings) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"items": []})

    search(settings, handler)

    assert seen[0].headers["X-Goog-Api-Key"] == KEY
    assert KEY not in str(seen[0].url)


def test_a_missing_key_sends_nothing(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("aucun appel attendu")

    with pytest.raises(MusicNotConfiguredError):
        search(settings, handler, key="")


def test_an_exhausted_quota_is_recognised(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"errors": [{"reason": "quotaExceeded"}]}})

    with pytest.raises(MusicQuotaError):
        search(settings, handler)


def test_a_network_failure_is_converted(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("coupure")

    with pytest.raises(MusicSourceError):
        search(settings, handler)
