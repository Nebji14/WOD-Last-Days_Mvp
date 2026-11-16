"""Connexion à PostgreSQL (Supabase) par un pool asyncpg."""

import asyncpg

from app.core.config import Settings

_MIN_CONNECTIONS = 1
_MAX_CONNECTIONS = 5
_COMMAND_TIMEOUT_SECONDS = 10.0


async def create_pool(settings: Settings) -> asyncpg.Pool:
    """Ouvre le pool de connexions.

    Le cache de requêtes préparées est désactivé : le pooler de Supabase en
    mode transaction ne le supporte pas.
    """
    return await asyncpg.create_pool(
        dsn=settings.database_url.get_secret_value(),
        min_size=_MIN_CONNECTIONS,
        max_size=_MAX_CONNECTIONS,
        command_timeout=_COMMAND_TIMEOUT_SECONDS,
        statement_cache_size=0,
        ssl="require",
    )
