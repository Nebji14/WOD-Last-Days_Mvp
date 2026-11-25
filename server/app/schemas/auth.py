"""Modèles d'entrée et de sortie des routes d'authentification."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.accounts import Account, Role

# Bornes larges : elles protègent le serveur des charges excessives. Les règles
# précises (format, sécurité) sont appliquées par le domaine, avec des codes
# d'erreur dédiés.
MAX_USERNAME_INPUT = 64
MAX_PASSWORD_INPUT = 256


class RegisterRequest(BaseModel):
    """Demande d'inscription d'un joueur."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    username: str = Field(min_length=1, max_length=MAX_USERNAME_INPUT)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_INPUT)
    password_confirmation: str = Field(min_length=1, max_length=MAX_PASSWORD_INPUT)


class LoginRequest(BaseModel):
    """Demande de connexion par nom d'utilisateur et mot de passe."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=MAX_USERNAME_INPUT)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_INPUT)


class LoginMethodsResponse(BaseModel):
    """Méthodes de connexion rattachées à un compte."""

    password: bool
    google: bool


class AccountResponse(BaseModel):
    """Compte tel qu'il est exposé au client. N'inclut aucune donnée interne."""

    id: UUID
    username: str
    display_name: str
    role: Role
    portrait: str | None

    @classmethod
    def from_account(cls, account: Account) -> "AccountResponse":
        """Projette un compte du domaine vers sa représentation publique."""
        return cls(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            role=account.role,
            portrait=account.portrait,
        )
