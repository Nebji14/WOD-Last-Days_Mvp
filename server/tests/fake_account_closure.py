"""Doublure des départs de joueurs, construite sur les doublures des comptes et du chat."""

from dataclasses import replace
from uuid import UUID, uuid4

from app.domain.accounts import AccountStatus, Role
from app.domain.chat import Notice
from app.repositories.account_closure import DeletedAccount
from tests.fake_characters import FakeCharacterStore
from tests.fakes import FakeAccountStore, FakeMessageStore


class FakeAccountClosureStore:
    """Reproduit l'annonce, l'effacement en cascade et les messages sans auteur."""

    def __init__(
        self, accounts: FakeAccountStore, characters: FakeCharacterStore, messages: FakeMessageStore
    ) -> None:
        self._accounts = accounts
        self._characters = characters
        self._messages = messages

    async def disable(self, account_id: UUID, body: str) -> UUID | None:
        account = self._accounts.accounts[account_id]
        if not account.is_active or account.role is not Role.PLAYER:
            return None
        message_id = await self._notice(account_id, body, Notice.DISABLED)
        self._accounts.disable(account_id)
        return message_id

    async def reactivate(self, account_id: UUID) -> bool:
        account = self._accounts.accounts.get(account_id)
        if account is None or account.is_active:
            return False
        self._accounts.accounts[account_id] = replace(account, status=AccountStatus.ACTIVE)
        return True

    async def delete(self, account_id: UUID, body: str) -> DeletedAccount | None:
        if account_id not in self._accounts.accounts:
            return None
        message_id = await self._notice(account_id, body, Notice.DELETED)
        owned = self._characters.owned_by(account_id)
        portraits = [s.portrait for c in owned for s in c.sheets if s.portrait is not None]
        for character in owned:
            await self._characters.delete(character.id)
        for message in list(self._messages.messages.values()):
            if message.author_id == account_id:
                self._messages.messages[message.id] = replace(
                    message, author_id=None, author_name=""
                )
        del self._accounts.accounts[account_id]
        return DeletedAccount(message_id, portraits)

    async def _notice(self, account_id: UUID, body: str, notice: Notice) -> UUID:
        message = await self._messages.create(account_id, uuid4(), body)
        self._messages.messages[message.id] = replace(message, notice=notice)
        return message.id
