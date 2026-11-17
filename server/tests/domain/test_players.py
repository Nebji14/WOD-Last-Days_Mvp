"""Ordre de la liste des joueurs dans l'outil Joueurs du MJ (Q04a-2)."""

from uuid import uuid4

from app.domain.accounts import Account, AccountStatus, Role
from app.domain.players import PlayerRecord, PlayerSummary, order_players


def _player(display_name: str, online: bool, username: str | None = None) -> PlayerSummary:
    account = Account(
        uuid4(),
        username or display_name.lower(),
        display_name,
        f"{uuid4()}@users.test",
        Role.PLAYER,
        AccountStatus.ACTIVE,
    )
    return PlayerSummary(record=PlayerRecord(account=account, character_names=()), online=online)


def _names(players: list[PlayerSummary]) -> list[str]:
    return [p.record.account.display_name for p in players]


def test_online_players_come_first_then_alphabetical_order() -> None:
    players = [_player("Tom", False), _player("léa", True), _player("Inès", False)]
    players.append(_player("Hugo", True))

    assert _names(order_players(players)) == ["Hugo", "léa", "Inès", "Tom"]


def test_alphabetical_order_ignores_case_and_uses_username_on_ties() -> None:
    second = _player("Sami", False, username="sami.b")
    first = _player("sami", False, username="sami.a")

    assert order_players([second, first]) == [first, second]
