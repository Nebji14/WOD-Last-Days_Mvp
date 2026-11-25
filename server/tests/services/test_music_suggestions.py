"""Suggestions de recherche : textes proposés, mémoire et pannes."""

import asyncio

from app.gateways.itunes import SongName
from app.services.music_suggestions import MusicSuggestionService, suggestions_from
from tests.fake_music import TIME, FakeClock, FakeSuggestionSource


def test_a_repeated_artist_comes_first_without_duplicates() -> None:
    songs = [
        SongName("Hans Zimmer", "Time"),
        SongName("HANS ZIMMER", "time"),
        SongName("Hans Zimmer", "Cornfield Chase"),
        SongName("Autre", "x" * 200),
    ]

    assert suggestions_from(songs) == [
        "Hans Zimmer",
        "Hans Zimmer - Time",
        "Hans Zimmer - Cornfield Chase",
    ]


def test_the_same_text_is_asked_once_until_it_expires() -> None:
    async def scenario() -> None:
        source, clock = FakeSuggestionSource(), FakeClock()
        service = MusicSuggestionService(source, clock)
        assert await service.suggest("Hans  Zimm") == [f"{TIME.artist} - {TIME.title}"]
        await service.suggest("hans zimm")
        assert source.queries == ["hans zimm"]

        clock.advance(25 * 3600.0)
        await service.suggest("hans zimm")
        assert len(source.queries) == 2

    asyncio.run(scenario())


def test_a_failure_gives_nothing_and_is_not_remembered() -> None:
    async def scenario() -> None:
        source = FakeSuggestionSource()
        service = MusicSuggestionService(source, FakeClock())
        source.available = False
        assert await service.suggest("hans") == []

        source.available = True
        assert await service.suggest("hans") != []

    asyncio.run(scenario())


def test_the_source_is_never_called_too_often() -> None:
    async def scenario() -> None:
        source, clock = FakeSuggestionSource(), FakeClock()
        service = MusicSuggestionService(source, clock)
        for index in range(30):
            await service.suggest(f"texte {index}")
        assert len(source.queries) == 18

        clock.advance(60.0)
        assert await service.suggest("autre") != []

    asyncio.run(scenario())
