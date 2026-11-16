"""Doublures de test : dépôt de comptes, fournisseur d'identité et vérificateur de jetons."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.core.security import InvalidTokenError, SessionTokens, TokenClaims
from app.domain.accounts import Account, AccountStatus, Role
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
        return TokenClaims(account_id=user_id)
