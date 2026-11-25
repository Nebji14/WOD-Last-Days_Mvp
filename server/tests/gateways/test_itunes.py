"""Client des suggestions : lecture des noms et pannes."""

import asyncio
from collections.abc import Callable

import httpx
import pytest

from app.gateways.itunes import ItunesGateway, SongName, SuggestionSourceError


def songs(handler: Callable[[httpx.Request], httpx.Response]) -> list[SongName]:
    async def run() -> list[SongName]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await ItunesGateway(client).songs("hans zimm")

    return asyncio.run(run())


def test_names_are_read_and_malformed_entries_skipped() -> None:
    results = [
        {"artistName": "Hans Zimmer", "trackName": "Time", "previewUrl": "https://x.test"},
        {"artistName": "Sans titre"},
        "inattendu",
    ]

    found = songs(lambda request: httpx.Response(200, json={"results": results}))

    assert found == [SongName("Hans Zimmer", "Time")]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403),
        httpx.Response(200, text="pas du JSON"),
        httpx.Response(200, json={"results": None}),
    ],
)
def test_a_refusal_is_converted(response: httpx.Response) -> None:
    with pytest.raises(SuggestionSourceError):
        songs(lambda request: response)
