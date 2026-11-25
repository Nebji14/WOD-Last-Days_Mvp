"""Places autour de la table."""

from uuid import uuid4

import pytest

from app.domain.table import PLAYER_SEAT_COUNT, SeatMap, TableFullError


def test_first_free_seat_is_assigned_in_order() -> None:
    seats = SeatMap()
    first, second = uuid4(), uuid4()

    seats.enter(first, "lea")
    seats.enter(second, "ben")

    assert [(s.position, s.account_id, s.online) for s in seats.seats()] == [
        (0, first, True),
        (1, second, True),
    ]


def test_player_keeps_seat_after_leaving_and_coming_back() -> None:
    seats = SeatMap()
    first, second = uuid4(), uuid4()
    seats.enter(first, "lea")
    seats.enter(second, "ben")

    seats.leave(first)
    assert [(s.position, s.online) for s in seats.seats()] == [(0, False), (1, True)]

    seats.enter(first, "lea")
    assert [(s.position, s.online) for s in seats.seats()] == [(0, True), (1, True)]


def test_player_is_online_while_one_connection_remains() -> None:
    seats = SeatMap()
    account = uuid4()
    seats.enter(account, "lea")
    seats.enter(account, "lea")

    seats.leave(account)
    assert seats.seats()[0].online is True

    seats.leave(account)
    assert seats.seats()[0].online is False


def test_renaming_a_player_keeps_the_seat() -> None:
    seats = SeatMap()
    account = uuid4()
    seats.enter(account, "lea")

    seats.rename(account, "Léa")
    seats.rename(uuid4(), "Inconnu")

    assert [(s.position, s.display_name) for s in seats.seats()] == [(0, "Léa")]


def test_vacating_frees_the_seat_for_someone_else() -> None:
    seats = SeatMap()
    first, second = uuid4(), uuid4()
    seats.enter(first, "lea")

    seats.vacate(first)
    seats.leave(first)
    seats.enter(second, "ben")

    assert [(s.position, s.account_id) for s in seats.seats()] == [(0, second)]


def test_leaving_without_having_entered_is_ignored() -> None:
    seats = SeatMap()

    seats.leave(uuid4())

    assert seats.seats() == []


def test_table_holds_nine_players() -> None:
    seats = SeatMap()
    for index in range(PLAYER_SEAT_COUNT):
        seats.enter(uuid4(), f"joueur{index}")

    with pytest.raises(TableFullError):
        seats.enter(uuid4(), "de trop")


def test_offline_player_keeps_seat_when_table_is_full() -> None:
    seats = SeatMap()
    accounts = [uuid4() for _ in range(PLAYER_SEAT_COUNT)]
    for account in accounts:
        seats.enter(account, "joueur")
    seats.leave(accounts[0])

    with pytest.raises(TableFullError):
        seats.enter(uuid4(), "de trop")
    seats.enter(accounts[0], "joueur")

    assert seats.seats()[0].online is True
