"""Piste de blessures : ordre sans trou, symboles et capacité maximale."""

import pytest

from app.domain.wounds import (
    NoSuchWoundError,
    TrackFullError,
    Wound,
    add_wound,
    heal_wound,
    is_valid_track,
    worsen_wound,
)


@pytest.mark.parametrize("track", ["", "*", "*X/", "**XX//", "///"])
def test_ordered_tracks_are_valid(track: str) -> None:
    assert is_valid_track(track, capacity=7)


@pytest.mark.parametrize("track", ["/X", "X*", "/*", "* X", "*?", "x"])
def test_unordered_or_unknown_tracks_are_invalid(track: str) -> None:
    assert not is_valid_track(track, capacity=7)


def test_track_longer_than_health_is_invalid() -> None:
    assert not is_valid_track("XXX", capacity=2)


@pytest.mark.parametrize(
    ("track", "wound", "expected"),
    [
        ("", Wound.BASHING, "/"),
        ("X/", Wound.BASHING, "X//"),
        ("X/", Wound.LETHAL, "XX/"),
        ("X/", Wound.AGGRAVATED, "*X/"),
        ("//", Wound.AGGRAVATED, "*//"),
    ],
)
def test_added_wound_is_filed_by_severity(track: str, wound: Wound, expected: str) -> None:
    assert add_wound(track, wound, capacity=7) == expected


@pytest.mark.parametrize(
    ("track", "wound", "expected"),
    [
        ("///////", Wound.BASHING, "X//////"),
        ("///////", Wound.LETHAL, "X//////"),
        ("XXXXXXX", Wound.LETHAL, "*XXXXXX"),
        ("XXXXXXX", Wound.BASHING, "*XXXXXX"),
        ("*XX////", Wound.AGGRAVATED, "**XX///"),
        ("*XXXXXX", Wound.BASHING, "**XXXXX"),
    ],
)
def test_full_track_worsens_the_least_severe_wound(track: str, wound: Wound, expected: str) -> None:
    assert add_wound(track, wound, capacity=7) == expected


def test_fully_aggravated_track_takes_no_more_wounds() -> None:
    with pytest.raises(TrackFullError):
        add_wound("***", Wound.BASHING, capacity=3)


def test_healing_removes_the_least_severe_wound_by_default() -> None:
    assert heal_wound("*X/") == "*X"
    assert heal_wound("*X") == "*"


def test_healing_a_given_kind_keeps_the_track_without_gap() -> None:
    assert heal_wound("*XX/", Wound.LETHAL) == "*X/"
    assert heal_wound("*X/", Wound.AGGRAVATED) == "X/"


def test_healing_a_missing_wound_is_refused() -> None:
    with pytest.raises(NoSuchWoundError):
        heal_wound("")
    with pytest.raises(NoSuchWoundError):
        heal_wound("//", Wound.LETHAL)


def test_worsening_moves_a_wound_up_one_step() -> None:
    assert worsen_wound("X//", Wound.BASHING) == "XX/"
    assert worsen_wound("X//", Wound.LETHAL) == "*//"


def test_worsening_needs_a_wound_that_can_get_worse() -> None:
    with pytest.raises(NoSuchWoundError):
        worsen_wound("*", Wound.AGGRAVATED)
    with pytest.raises(NoSuchWoundError):
        worsen_wound("*", Wound.BASHING)


def test_every_operation_keeps_the_track_valid() -> None:
    track = ""
    for wound in (Wound.BASHING, Wound.AGGRAVATED, Wound.LETHAL, Wound.BASHING):
        track = add_wound(track, wound, capacity=5)
    track = worsen_wound(track, Wound.BASHING)
    track = heal_wound(track, Wound.AGGRAVATED)

    assert track == "XX/"
    assert is_valid_track(track, capacity=5)
