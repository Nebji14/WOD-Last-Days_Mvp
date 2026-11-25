"""Enchaînement automatique et mémoire du catalogue de musique."""

import asyncio

import pytest

from app.core.errors import AppError, ErrorCode
from app.domain.music import Track
from app.gateways.youtube import MusicNotConfiguredError, MusicQuotaError, MusicSourceError
from app.services.music import MusicService, NowPlaying
from app.services.music_catalog import MusicCatalog
from tests.fake_music import DOCKS, HUNT, FakeClock, FakeMusicSource


class _Recorder:
    """Retient les états diffusés."""

    def __init__(self) -> None:
        self.states: list[NowPlaying] = []

    async def music_changed(self, now: NowPlaying) -> None:
        self.states.append(now)


def test_the_next_track_starts_when_the_current_one_is_over() -> None:
    async def scenario() -> None:
        clock, recorder = FakeClock(), _Recorder()
        service = MusicService(recorder, clock)
        await service.play_all([HUNT, DOCKS], shuffled=False)

        clock.advance(179.0)
        assert not await service.finish_if_over()
        clock.advance(1.0)
        assert await service.finish_if_over()

        assert recorder.states[-1].track == DOCKS
        assert recorder.states[-1].playing
        service.close()

    asyncio.run(scenario())


def test_the_timer_chains_without_any_command() -> None:
    async def scenario() -> None:
        clock, recorder = FakeClock(), _Recorder()
        service = MusicService(recorder, clock)
        await service.play_all([HUNT, DOCKS], shuffled=False)
        # Position à la fin du morceau : la minuterie se déclenche aussitôt.
        await service.seek(float(HUNT.duration_seconds))
        await asyncio.sleep(0.05)

        assert recorder.states[-1].track == DOCKS
        service.close()

    asyncio.run(scenario())


def test_a_paused_track_never_ends() -> None:
    async def scenario() -> None:
        clock = FakeClock()
        service = MusicService(_Recorder(), clock)
        await service.play(HUNT)
        await service.pause()
        clock.advance(10_000.0)

        assert not await service.finish_if_over()
        service.close()

    asyncio.run(scenario())


def test_skipping_twice_the_same_play_skips_one_track() -> None:
    async def scenario() -> None:
        service = MusicService(_Recorder(), FakeClock())
        await service.play_all([HUNT, DOCKS, HUNT], shuffled=False)
        play_id = service.now_playing().play_id
        await service.skip(play_id)
        await service.skip(play_id)

        assert service.now_playing().track == DOCKS
        service.close()

    asyncio.run(scenario())


def test_the_same_search_is_sent_once_until_it_expires() -> None:
    async def scenario() -> None:
        source, clock = FakeMusicSource(), FakeClock()
        catalog = MusicCatalog(source, clock)
        await catalog.search("Docks")
        await catalog.search("  docks ")
        assert source.searches == ["docks"]

        clock.advance(25 * 3600.0)
        await catalog.search("docks")
        assert source.searches == ["docks", "docks"]

    asyncio.run(scenario())


def test_a_found_track_is_not_described_again() -> None:
    async def scenario() -> Track:
        source = FakeMusicSource()
        catalog = MusicCatalog(source, FakeClock())
        await catalog.search("docks")
        track = await catalog.track(DOCKS.video_id)
        assert source.descriptions == []
        return track

    assert asyncio.run(scenario()) == DOCKS


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (MusicNotConfiguredError(), ErrorCode.MUSIC_NOT_CONFIGURED),
        (MusicQuotaError(), ErrorCode.MUSIC_QUOTA_REACHED),
        (MusicSourceError(), ErrorCode.SERVICE_UNAVAILABLE),
    ],
)
def test_source_failures_are_explained(error: MusicSourceError, code: ErrorCode) -> None:
    source = FakeMusicSource()
    source.error = error

    with pytest.raises(AppError) as caught:
        asyncio.run(MusicCatalog(source, FakeClock()).search("docks"))

    assert caught.value.code is code
