"""Création du compte MJ.

À exécuter une seule fois, depuis le dossier ``server`` ::

    python -m scripts.create_gm

L'identifiant, l'adresse de récupération et le mot de passe sont lus dans les
variables ``GM_USERNAME``, ``GM_EMAIL`` et ``GM_PASSWORD`` (environnement ou
fichier ``.env``). Si l'une d'elles manque, les trois sont demandées au clavier.
Dans les deux cas, elles ne figurent ni dans le code, ni dans l'historique des
commandes. Les trois lignes sont à retirer du fichier ``.env`` après la création.
"""

import asyncio
import getpass
import sys

import httpx
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

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
                gm_access_path=settings.gm_access_path,
            )
            account = await service.create_gm(username, email, password)
    finally:
        await pool.close()
    print(f"Compte MJ créé : {account.username}")


class _GmSeed(BaseSettings):
    """Identifiants du compte MJ fournis par l'environnement ou le fichier ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gm_username: str = ""
    gm_email: str = ""
    gm_password: SecretStr = SecretStr("")


def _read_credentials() -> tuple[str, str, str] | None:
    """Retourne (identifiant, adresse, mot de passe), ou ``None`` si la saisie est incohérente."""
    seed = _GmSeed()
    password = seed.gm_password.get_secret_value()
    if seed.gm_username and seed.gm_email and password:
        return seed.gm_username.strip(), seed.gm_email.strip(), password
    username = input("Identifiant du MJ : ").strip()
    email = input("Adresse e-mail de récupération : ").strip()
    password = getpass.getpass("Mot de passe : ")
    if password != getpass.getpass("Confirmer le mot de passe : "):
        return None
    return username, email, password


def main() -> int:
    """Lit les identifiants et lance la création."""
    credentials = _read_credentials()
    if credentials is None:
        print("Les deux mots de passe sont différents.", file=sys.stderr)
        return 1
    username, email, password = credentials
    try:
        asyncio.run(_create_gm(username, email, password))
    except AppError as exc:
        details = ", ".join(str(item.get("rule")) for item in exc.details or [])
        print(f"Création refusée : {exc.message} {details}".rstrip(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
