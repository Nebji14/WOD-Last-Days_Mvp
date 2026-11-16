"""Doublures de test : dépôts en mémoire, fournisseur d'identité et vérificateur de jetons."""

import time
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.security import InvalidTokenError, SessionTokens, TokenClaims
from app.domain.accounts import Account, AccountStatus, Role
from app.domain.chat import ChatMessage
from app.gateways.supabase_auth import IdentityAlreadyExistsError, InvalidCredentialsError
from app.repositories.accounts import UsernameAlreadyExistsError


class FakeAccountStore:
    """Dépôt de comptes en mémoire, avec les mêmes unicités que la base."""

    def __init__(self) -> None:
        self.accounts: dict[UUID, Account] = {}

    async def get_by_id(self, account_id: UUID) -> Account | None:
        return self.accounts.get(account_id)

    async def get_by_username(self, username: str) -> Account | None:
        wanted = username.lower()
        return next((a for a in self.accounts.values() if a.username.lower() == wanted), None)

    async def get_gm(self) -> Account | None:
        return next((a for a in self.accounts.values() if a.role is Role.GM), None)

    async def create(
        self, *, account_id: UUID, username: str, display_name: str, auth_email: str, role: Role
    ) -> Account:
        gm_exists = any(a.role is Role.GM for a in self.accounts.values())
        if await self.get_by_username(username) or (role is Role.GM and gm_exists):
            raise UsernameAlreadyExistsError
        account = Account(
            account_id, username, display_name, auth_email, role, AccountStatus.ACTIVE
        )
        self.accounts[account_id] = account
        return account

    def disable(self, account_id: UUID) -> None:
        current = self.accounts[account_id]
        self.accounts[account_id] = Account(
            current.id,
            current.username,
            current.display_name,
            current.auth_email,
            current.role,
            AccountStatus.DISABLED,
        )


@dataclass
class FakeIdentityProvider:
    """Fournisseur d'identité en mémoire. Les jetons émis sont opaques."""

    users: dict[str, tuple[UUID, str]] = field(default_factory=dict)
    sessions: dict[str, UUID] = field(default_factory=dict)
    refresh_tokens: dict[str, UUID] = field(default_factory=dict)
    deleted: list[UUID] = field(default_factory=list)

    async def create_user(self, email: str, password: str) -> UUID:
        if email in self.users:
            raise IdentityAlreadyExistsError
        user_id = uuid4()
        self.users[email] = (user_id, password)
        return user_id

    async def delete_user(self, user_id: UUID) -> None:
        self.deleted.append(user_id)
        self.users = {email: user for email, user in self.users.items() if user[0] != user_id}

    async def sign_in(self, email: str, password: str) -> SessionTokens:
        user = self.users.get(email)
        if user is None or user[1] != password:
            raise InvalidCredentialsError
        return self._open_session(user[0])

    async def refresh(self, refresh_token: str) -> SessionTokens:
        user_id = self.refresh_tokens.pop(refresh_token, None)
        if user_id is None:
            raise InvalidCredentialsError
        return self._open_session(user_id)

    async def sign_out(self, access_token: str) -> None:
        self.sessions.pop(access_token, None)

    def _open_session(self, user_id: UUID) -> SessionTokens:
        access, refresh = f"access-{uuid4().hex}", f"refresh-{uuid4().hex}"
        self.sessions[access] = user_id
        self.refresh_tokens[refresh] = user_id
        return SessionTokens(access_token=access, refresh_token=refresh, expires_in=3600)


class FakeTokenVerifier:
    """Reconnaît les jetons émis par ``FakeIdentityProvider`` et encore ouverts."""

    def __init__(self, identity: FakeIdentityProvider) -> None:
        self._identity = identity

    async def verify(self, token: str) -> TokenClaims:
        user_id = self._identity.sessions.get(token)
        if user_id is None:
            raise InvalidTokenError
        return TokenClaims(account_id=user_id, expires_at=time.time() + 3600)


class FakeMessageStore:
    """Dépôt de messages en mémoire, avec l'envoi idempotent de la base."""

    def __init__(self, accounts: FakeAccountStore) -> None:
        self._accounts = accounts
        self.messages: dict[UUID, ChatMessage] = {}
        self._tokens: dict[tuple[UUID, UUID], UUID] = {}

    async def get(self, message_id: UUID) -> ChatMessage | None:
        return self.messages.get(message_id)

    async def list_page(self, before: int | None, limit: int) -> list[ChatMessage]:
        ordered = sorted(self.messages.values(), key=lambda m: m.position, reverse=True)
        return [m for m in ordered if before is None or m.position < before][:limit]

    async def create(self, author_id: UUID, client_token: UUID, body: str) -> ChatMessage:
        existing = self._tokens.get((author_id, client_token))
        if existing is not None:
            return self.messages[existing]
        author = self._accounts.accounts[author_id]
        message = ChatMessage(
            id=uuid4(),
            position=len(self.messages) + 1,
            author_id=author_id,
            author_name=author.display_name,
            author_role=author.role,
            body=body,
            sent_at=datetime.now(UTC),
            edited_at=None,
            deleted_by_role=None,
        )
        self.messages[message.id] = message
        self._tokens[(author_id, client_token)] = message.id
        return message

    async def update_body(self, message_id: UUID, body: str) -> ChatMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.is_deleted:
            return None
        self.messages[message_id] = replace(message, body=body, edited_at=datetime.now(UTC))
        return self.messages[message_id]

    async def mark_deleted(self, message_id: UUID, deleted_by: UUID) -> ChatMessage | None:
        message = self.messages.get(message_id)
        if message is None or message.is_deleted:
            return None
        role = self._accounts.accounts[deleted_by].role
        self.messages[message_id] = replace(message, body=None, deleted_by_role=role)
        return self.messages[message_id]
