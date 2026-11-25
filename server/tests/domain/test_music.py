"""Règles de la musique : liens, durées, position et enchaînement."""

import pytest

from app.domain.music import (
    QUEUE_MAX,
    MusicDeck,
    QueueFullError,
    RepeatMode,
    UnknownItemError,
    duration_seconds,
    video_id_from_link,
)
from tests.fake_music import DAWN, DOCKS, HUNT


@pytest.mark.parametrize(
    "link",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?list=PL1&v=dQw4w9WgXcQ&t=12s",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc",
        "youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "  https://www.youtube.com/embed/dQw4w9WgXcQ  ",
    ],
)
def test_a_pasted_link_gives_its_video(link: str) -> None:
    assert video_id_from_link(link) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "text",
    [
        "musique de combat",
        "dQw4w9WgXcQ",
        "https://example.org/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com.example.org/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=court",
        "https://www.youtube.com/playlist?list=PL1",
        "https://[",
        "",
    ],
)
def test_other_texts_are_not_links(text: str) -> None:
    assert video_id_from_link(text) is None


@pytest.mark.parametrize(
    ("value", "seconds"),
    [
        ("PT4M13S", 253),
        ("PT1H2M3S", 3723),
        ("P1DT1S", 86401),
        ("PT45S", 45),
        ("P0D", 0),
        ("inconnu", 0),
    ],
)
def test_duration(value: str, seconds: int) -> None:
    assert duration_seconds(value) == seconds


def test_position_follows_the_clock_and_stops_at_the_end() -> None:
    deck = MusicDeck()
    deck.play(HUNT, now=100.0)

    assert deck.position(130.0) == 30.0
    assert deck.remaining(130.0) == 150.0
    assert deck.position(1000.0) == 180.0


def test_pause_freezes_the_position_and_resume_continues() -> None:
    deck = MusicDeck()
    deck.play(HUNT, now=0.0)
    deck.pause(now=20.0)

    assert deck.position(500.0) == 20.0
    assert deck.remaining(500.0) is None

    deck.resume(now=500.0)
    assert deck.position(510.0) == 30.0


def test_seek_is_bounded_and_keeps_the_pause() -> None:
    deck = MusicDeck()
    deck.play(HUNT, now=0.0)
    deck.pause(now=10.0)
    deck.seek(9999.0, now=20.0)

    assert deck.position(50.0) == 180.0
    assert not deck.is_playing


def test_enqueue_starts_when_nothing_plays_then_waits() -> None:
    deck = MusicDeck()
    deck.enqueue(HUNT, now=0.0)
    deck.enqueue(DOCKS, now=0.0)

    assert deck.current is not None
    assert deck.current.track == HUNT
    assert [item.track for item in deck.queue] == [DOCKS]


def test_playing_now_keeps_the_queue() -> None:
    deck = MusicDeck()
    deck.enqueue(HUNT, now=0.0)
    deck.enqueue(DOCKS, now=0.0)
    deck.play(DAWN, now=5.0)

    assert deck.current is not None
    assert deck.current.track == DAWN
    assert [item.track for item in deck.queue] == [DOCKS]


def test_finish_chains_then_stops() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS], now=0.0)
    deck.finish(now=180.0)

    assert deck.current is not None
    assert deck.current.track == DOCKS
    assert deck.position(180.0) == 0.0

    deck.finish(now=420.0)
    assert deck.current is None
    assert not deck.is_playing


def test_repeating_a_track_gives_a_new_play() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS], now=0.0)
    deck.repeat = RepeatMode.TRACK
    first = deck.play_id
    deck.finish(now=180.0)

    assert deck.current is not None
    assert deck.current.track == HUNT
    assert deck.play_id != first


def test_skip_leaves_a_repeated_track() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS], now=0.0)
    deck.repeat = RepeatMode.TRACK
    deck.skip(now=10.0)

    assert deck.current is not None
    assert deck.current.track == DOCKS


def test_repeating_the_queue_never_ends() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS], now=0.0)
    deck.repeat = RepeatMode.QUEUE

    played = []
    for now in (1.0, 2.0, 3.0):
        deck.finish(now)
        assert deck.current is not None
        played.append(deck.current.track)

    assert played == [DOCKS, HUNT, DOCKS]


def test_queue_items_move_play_and_leave() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS, DAWN], now=0.0)
    dawn = deck.queue[1]
    deck.move(dawn.id, 0)
    assert [item.track for item in deck.queue] == [DAWN, DOCKS]

    deck.play_item(dawn.id, now=5.0)
    assert deck.current == dawn
    assert [item.track for item in deck.queue] == [DOCKS]

    deck.remove(deck.queue[0].id)
    assert deck.queue == []
    with pytest.raises(UnknownItemError):
        deck.remove(dawn.id)


def test_stopping_keeps_the_queue() -> None:
    deck = MusicDeck()
    deck.play_all([HUNT, DOCKS], now=0.0)
    deck.stop()

    assert deck.current is None
    assert len(deck.queue) == 1


def test_the_next_track_starts_without_its_video() -> None:
    deck = MusicDeck()
    deck.play(HUNT, now=0.0, show_video=True)
    deck.enqueue(DOCKS, now=0.0)
    deck.repeat = RepeatMode.TRACK
    deck.finish(now=180.0)
    assert deck.video_shown

    deck.skip(now=190.0)
    assert not deck.video_shown


def test_nothing_is_shown_without_a_track() -> None:
    deck = MusicDeck()
    deck.show_video(True)
    assert not deck.video_shown

    deck.play(HUNT, now=0.0, show_video=True)
    deck.stop()
    assert not deck.video_shown


def test_the_queue_is_bounded() -> None:
    deck = MusicDeck()
    for _ in range(QUEUE_MAX + 1):
        deck.enqueue(HUNT, now=0.0)

    with pytest.raises(QueueFullError):
        deck.enqueue(HUNT, now=0.0)
