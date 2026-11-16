"""Accès aux données des comptes (table ``account``)."""

from uuid import UUID

import asyncpg

from app.domain.accounts import Account, AccountStatus, Role

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
        """Retourne le compte du MJ (unique, C01), ou ``None`` s'il n'est pas créé."""
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
                déjà pris, ou si un compte MJ existe déjà (C01).
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
