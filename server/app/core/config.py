"""Configuration du serveur, lue depuis les variables d'environnement.

Aucun secret n'a de valeur par défaut : le serveur refuse de démarrer si une
variable obligatoire est absente.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres d'exécution du serveur.

    Attributs:
        environment: ``production`` active les cookies ``Secure`` et HSTS, et
            désactive la documentation interactive.
        supabase_url: adresse du projet Supabase, sans barre oblique finale.
        supabase_publishable_key: clé publique, utilisée pour les appels
            d'authentification au nom d'un utilisateur.
        supabase_secret_key: clé d'administration ; ne quitte jamais le serveur.
        database_url: chaîne de connexion PostgreSQL.
        allowed_origins: origines autorisées pour CORS et le contrôle d'origine.
        session_idle_seconds: durée d'inactivité avant expiration (CDC 12.2).
        technical_email_domain: domaine des adresses techniques associées aux
            noms d'utilisateur des joueurs (décision T-3).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: SecretStr
    database_url: SecretStr
    allowed_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    session_idle_seconds: int = Field(default=7200, ge=300, le=86400)
    technical_email_domain: str = "users.hunter.local"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accepte une liste séparée par des virgules."""
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("supabase_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def is_production(self) -> bool:
        """Indique si le serveur tourne en production."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Retourne la configuration, chargée une seule fois par processus."""
    return Settings()
