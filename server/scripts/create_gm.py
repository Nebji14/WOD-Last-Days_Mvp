"""Création du compte MJ (décision T-5).

À exécuter une seule fois, depuis le dossier ``server`` ::

    python -m scripts.create_gm

L'identifiant, l'adresse de récupération et le mot de passe sont demandés au
clavier : ils ne figurent ni dans le code, ni dans l'historique des commandes.
"""

import asyncio
import getpass
import sys

import httpx

from app.core.config import get_settings
from app.core.database import create_pool
from app.core.errors import AppError
from app.gateways.supabase_auth import SupabaseAuthGateway
from app.repositories.accounts import PgAccountRepository
from app.services.auth import AuthService


async def _create_gm(username: str, email: str, password: str) -> None:
    """Assemble les services réels et crée le compte MJ."""
    settings = get_settings()
    pool = await create_pool(settings)
    try:
        async with httpx.AsyncClient() as client:
            service = AuthService(
                accounts=PgAccountRepository(pool),
                identity=SupabaseAuthGateway(settings, client),
                technical_email_domain=settings.technical_email_domain,
            )
            account = await service.create_gm(username, email, password)
    finally:
        await pool.close()
    print(f"Compte MJ créé : {account.username}")


def main() -> int:
    """Lit les informations au clavier et lance la création."""
    username = input("Identifiant du MJ : ").strip()
    email = input("Adresse e-mail de récupération : ").strip()
    password = getpass.getpass("Mot de passe : ")
    if password != getpass.getpass("Confirmer le mot de passe : "):
        print("Les deux mots de passe sont différents.", file=sys.stderr)
        return 1
    try:
        asyncio.run(_create_gm(username, email, password))
    except AppError as exc:
        details = ", ".join(str(item.get("rule")) for item in exc.details or [])
        print(f"Création refusée : {exc.message} {details}".rstrip(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
