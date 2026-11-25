"""Accès aux données des comptes (table ``account``)."""

from uuid import UUID

import asyncpg

from app.domain.accounts import Account, AccountStatus, LoginMethods, Role

_COLUMNS = "id, username, display_name, auth_email, role, status"


class UsernameAlreadyExistsError(Exception):
    """Un compte porte déjà ce nom d'utilisateur (casse ignorée)."""


class PgAccountRepository:
    """Dépôt des comptes sur PostgreSQL.

    Args:
        pool: pool de connexions asyncpg.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_by_id(self, account_id: UUID) -> Account | None:
        """Retourne le compte portant cet identifiant, ou ``None``."""
        row = await self._pool.fetchrow(
            f"select {_COLUMNS} from account where id = $1",  # noqa: S608 - colonnes constantes
            account_id,
        )
        return _to_account(row) if row else None

    async def get_by_username(self, username: str) -> Account | None:
        """Retourne le compte portant ce nom d'utilisateur, sans tenir compte de la casse."""
        row = await self._pool.fetchrow(
            f"select {_COLUMNS} from account where lower(username) = lower($1)",  # noqa: S608
            username,
        )
        return _to_account(row) if row else None

    async def get_gm(self) -> Account | None:
        """Retourne le compte du MJ (il n'y en a qu'un), ou ``None`` s'il n'est pas créé."""
        row = await self._pool.fetchrow(
            f"select {_COLUMNS} from account where role = 'gm'"  # noqa: S608
        )
        return _to_account(row) if row else None

    async def create(
        self,
        *,
        account_id: UUID,
        username: str,
        display_name: str,
        auth_email: str,
        role: Role,
    ) -> Account:
        """Crée un compte.

        Raises:
            UsernameAlreadyExistsError: si le nom d'utilisateur ou l'adresse est
                déjà pris, ou si un compte MJ existe déjà.
        """
        try:
            row = await self._pool.fetchrow(
                f"""
                insert into account (id, username, display_name, auth_email, role)
                values ($1, $2, $3, $4, $5)
                returning {_COLUMNS}
                """,  # noqa: S608
                account_id,
                username,
                display_name,
                auth_email,
                role.value,
            )
        except asyncpg.UniqueViolationError as exc:
            raise UsernameAlreadyExistsError from exc
        return _to_account(row)

    async def login_methods(self, account_id: UUID) -> LoginMethods:
        """Méthodes de connexion utilisables, lues dans les tables d'authentification."""
        row = await self._pool.fetchrow(
            """
            select coalesce(u.encrypted_password, '') <> '' as has_password,
                   exists (
                       select 1 from auth.identities i
                       where i.user_id = u.id and i.provider = 'google'
                   ) as has_google
            from auth.users u
            where u.id = $1
            """,
            account_id,
        )
        if row is None:
            return LoginMethods(password=False, google=False)
        return LoginMethods(password=row["has_password"], google=row["has_google"])

    async def is_display_name_taken(self, display_name: str, account_id: UUID) -> bool:
        """Indique si un autre compte porte déjà ce nom, affiché ou d'utilisateur."""
        taken: bool = await self._pool.fetchval(
            """
            select exists (
                select 1 from account
                where id <> $2 and lower($1) in (lower(display_name), lower(username))
            )
            """,
            display_name,
            account_id,
        )
        return taken

    async def update_names(
        self, account_id: UUID, username: str | None, display_name: str | None
    ) -> Account:
        """Modifie les noms d'un compte ; ``None`` conserve la valeur.

        Raises:
            UsernameAlreadyExistsError: si le nom d'utilisateur est déjà pris.
        """
        try:
            row = await self._pool.fetchrow(
                f"""
                update account
                set username = coalesce($2, username),
                    display_name = coalesce($3, display_name)
                where id = $1
                returning {_COLUMNS}
                """,  # noqa: S608
                account_id,
                username,
                display_name,
            )
        except asyncpg.UniqueViolationError as exc:
            raise UsernameAlreadyExistsError from exc
        return _to_account(row)

    async def update_auth_email(self, account_id: UUID, auth_email: str) -> None:
        """Recopie l'adresse de connexion connue du fournisseur d'identité."""
        await self._pool.execute(
            "update account set auth_email = $2 where id = $1", account_id, auth_email
        )


def _to_account(row: asyncpg.Record) -> Account:
    """Convertit une ligne de la table en objet du domaine."""
    return Account(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        auth_email=row["auth_email"],
        role=Role(row["role"]),
        status=AccountStatus(row["status"]),
    )
