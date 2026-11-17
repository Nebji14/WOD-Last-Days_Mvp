"""Doublure du dépôt des joueurs, construite sur les comptes et personnages en mémoire."""

from app.domain.accounts import Role
from app.domain.players import PlayerRecord
from tests.fake_characters import FakeCharacterStore
from tests.fakes import FakeAccountStore


class FakePlayerStore:
    """Comptes joueurs et noms de leurs personnages, dans l'ordre de création."""

    def __init__(self, accounts: FakeAccountStore, characters: FakeCharacterStore) -> None:
        self._accounts = accounts
        self._characters = characters

    async def list_players(self) -> list[PlayerRecord]:
        return [
            PlayerRecord(
                account=account,
                character_names=tuple(
                    c.main_sheet.texts["name"] for c in self._characters.owned_by(account.id)
                ),
            )
            for account in self._accounts.accounts.values()
            if account.role is Role.PLAYER
        ]
