"""Modèles d'entrée et de sortie des routes de gestion du compte."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import MAX_PASSWORD_INPUT, MAX_USERNAME_INPUT

_MAX_DISPLAY_NAME_INPUT = 120


class UpdateAccountRequest(BaseModel):
    """Noms à modifier ; un champ absent garde sa valeur."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1, max_length=MAX_USERNAME_INPUT)
    display_name: str | None = Field(default=None, min_length=1, max_length=_MAX_DISPLAY_NAME_INPUT)


class OwnerConfirmationRequest(BaseModel):
    """Confirmation du titulaire ; un compte sans mot de passe n'en envoie pas."""

    model_config = ConfigDict(extra="forbid")

    current_password: str | None = Field(default=None, max_length=MAX_PASSWORD_INPUT)


class ChangePasswordRequest(OwnerConfirmationRequest):
    """Nouveau mot de passe et sa confirmation."""

    password: str = Field(min_length=1, max_length=MAX_PASSWORD_INPUT)
    password_confirmation: str = Field(min_length=1, max_length=MAX_PASSWORD_INPUT)


class CloseAccountRequest(OwnerConfirmationRequest):
    """Départ d'un joueur : son nom d'utilisateur, recopié à l'identique."""

    username: str = Field(min_length=1, max_length=MAX_USERNAME_INPUT)


class GoogleUrlResponse(BaseModel):
    """Adresse de Google où envoyer le navigateur."""

    url: str
