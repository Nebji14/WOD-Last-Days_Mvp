"""Doublures de test : dépôts en mémoire, fournisseur d'identité et vérificateur de jetons."""

import time
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.security import InvalidTokenError, SessionTokens, TokenClaims, pkce_challenge
from app.domain.accounts import Account, AccountStatus, LoginMethods, Role
from app.domain.chat import ChatMessage
from app.gateways.supabase_auth import (
    ExternalIdentity,
    IdentityAlreadyExistsError,
    InvalidCredentialsError,
    LinkedIdentity,
)
from app.repositories.accounts import UsernameAlreadyExistsError


class FakeAccountStore:
    """Dépôt de comptes en mémoire, avec les mêmes unicités que la base."""

    def __init__(self) -> None:
        self.accounts: dict[UUID, Account] = {}
        self.identity: FakeIdentityProvider | None = None

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

    async def login_methods(self, account_id: UUID) -> LoginMethods:
        assert self.identity is not None
        return self.identity.methods_of(account_id)

    async def is_display_name_taken(self, display_name: str, account_id: UUID) -> bool:
        wanted = display_name.lower()
        return any(
            wanted in (a.display_name.lower(), a.username.lower())
            for a in self.accounts.values()
            if a.id != account_id
        )

    async def update_names(
        self, account_id: UUID, username: str | None, display_name: str | None
    ) -> Account:
        current = self.accounts[account_id]
        holder = await self.get_by_username(username) if username else None
        if holder is not None and holder.id != account_id:
            raise UsernameAlreadyExistsError
        self.accounts[account_id] = replace(
            current,
            username=username or current.username,
            display_name=display_name or current.display_name,
        )
        return self.accounts[account_id]

    async def update_auth_email(self, account_id: UUID, auth_email: str) -> None:
        self.accounts[account_id] = replace(self.accounts[account_id], auth_email=auth_email)

    def disable(self, account_id: UUID) -> None:
        self.accounts[account_id] = replace(
            self.accounts[account_id], status=AccountStatus.DISABLED
        )


@dataclass
class FakeIdentityProvider:
    """Fournisseur d'identité en mémoire. Les jetons émis sont opaques."""

    users: dict[str, tuple[UUID, str]] = field(default_factory=dict)
    sessions: dict[str, UUID] = field(default_factory=dict)
    refresh_tokens: dict[str, UUID] = field(default_factory=dict)
    deleted: list[UUID] = field(default_factory=list)
    # Connexion Google : empreintes PKCE reçues au départ, codes délivrés au retour.
    challenges: set[str] = field(default_factory=set)
    google_codes: dict[str, ExternalIdentity] = field(default_factory=dict)
    # Comptes Google rattachés à chaque utilisateur, du plus ancien au plus récent.
    google_links: dict[UUID, list[LinkedIdentity]] = field(default_factory=dict)
    google_identities: dict[str, ExternalIdentity] = field(default_factory=dict)
    # Date de connexion de chaque session, relue par le vérificateur de jetons.
    authenticated_at: dict[str, float] = field(default_factory=dict)
    link_requests: int = 0

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

    async def sign_out_others(self, access_token: str) -> None:
        user_id = self.sessions[access_token]
        self.sessions = {
            token: owner
            for token, owner in self.sessions.items()
            if owner != user_id or token == access_token
        }

    async def set_password(self, user_id: UUID, password: str, email: str | None = None) -> None:
        known = next((mail for mail, user in self.users.items() if user[0] == user_id), email)
        assert known is not None
        self.users[known] = (user_id, password)

    def methods_of(self, user_id: UUID) -> LoginMethods:
        return LoginMethods(
            password=any(user[0] == user_id for user in self.users.values()),
            google=bool(self.google_links.get(user_id)),
        )

    async def link_url(
        self, access_token: str, provider: str, redirect_to: str, code_challenge: str
    ) -> str:
        assert access_token in self.sessions
        self.link_requests += 1
        self.challenges.add(code_challenge)
        return f"https://example.supabase.co/auth/v1/link?provider={provider}"

    async def linked_identities(self, access_token: str) -> list[LinkedIdentity]:
        return list(self.google_links.get(self.sessions[access_token], []))

    async def unlink_identity(self, access_token: str, identity_id: UUID) -> None:
        links = self.google_links[self.sessions[access_token]]
        links[:] = [link for link in links if link.identity_id != identity_id]

    def authorize_url(self, provider: str, redirect_to: str, code_challenge: str) -> str:
        self.challenges.add(code_challenge)
        return f"https://example.supabase.co/auth/v1/authorize?provider={provider}"

    async def exchange_code(self, auth_code: str, code_verifier: str) -> SessionTokens:
        identity = self.google_codes.pop(auth_code, None)
        if identity is None or pkce_challenge(code_verifier) not in self.challenges:
            raise InvalidCredentialsError
        self._add_google_link(identity.user_id, linking=self.link_requests > 0)
        self.link_requests = 0
        tokens = self._open_session(identity.user_id)
        self.google_identities[tokens.access_token] = identity
        return tokens

    async def get_user(self, access_token: str) -> ExternalIdentity:
        known = self.google_identities.get(access_token)
        if known is not None:
            return known
        user_id = self.sessions[access_token]
        email = next(mail for mail, user in self.users.items() if user[0] == user_id)
        return ExternalIdentity(user_id=user_id, email=email, full_name=None)

    def _add_google_link(self, user_id: UUID, *, linking: bool) -> None:
        """Une première connexion ou un rattachement ajoute un compte Google."""
        links = self.google_links.setdefault(user_id, [])
        if linking or not links:
            links.append(LinkedIdentity(uuid4(), "google", datetime.now(UTC)))

    def _open_session(self, user_id: UUID) -> SessionTokens:
        access, refresh = f"access-{uuid4().hex}", f"refresh-{uuid4().hex}"
        self.sessions[access] = user_id
        self.authenticated_at[access] = time.time()
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
        return TokenClaims(
            account_id=user_id,
            expires_at=time.time() + 3600,
            authenticated_at=self._identity.authenticated_at.get(token),
        )


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

    async def create(
        self, author_id: UUID, client_token: UUID, body: str, roll: dict[str, Any] | None = None
    ) -> ChatMessage:
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
            roll=roll,
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
