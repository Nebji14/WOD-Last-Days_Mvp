"""Aller-retour vers Google en cours, gardé dans un cookie jusqu'au retour."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.core.security import new_pkce_verifier
from app.domain.accounts import Role

_FIELD_COUNT = 4


class GooglePurpose(StrEnum):
    """Raison du départ vers Google."""

    LOGIN = "login"
    LINK = "link"
    CONFIRM = "confirm"


@dataclass(frozen=True, slots=True)
class GoogleFlow:
    """Départ vers Google.

    Attributs:
        portal: page de départ (joueurs ou MJ), qui décide du retour en cas d'erreur.
        verifier: secret PKCE ; sans lui, le code reçu au retour est inutilisable.
        account_id: compte déjà connecté, pour un rattachement ou une confirmation.
    """

    portal: Role
    verifier: str
    purpose: GooglePurpose = GooglePurpose.LOGIN
    account_id: UUID | None = None

    @classmethod
    def new(
        cls,
        portal: Role,
        purpose: GooglePurpose = GooglePurpose.LOGIN,
        account_id: UUID | None = None,
    ) -> "GoogleFlow":
        """Prépare un départ avec un secret neuf."""
        return cls(portal, new_pkce_verifier(), purpose, account_id)

    def encode(self) -> str:
        """Valeur du cookie."""
        account = "" if self.account_id is None else str(self.account_id)
        return f"{self.portal.value}.{self.purpose.value}.{account}.{self.verifier}"

    @classmethod
    def decode(cls, value: str | None) -> "GoogleFlow | None":
        """Relit le cookie ; ``None`` s'il est absent ou altéré."""
        parts = (value or "").split(".")
        if len(parts) != _FIELD_COUNT or not parts[3]:
            return None
        try:
            portal, purpose = Role(parts[0]), GooglePurpose(parts[1])
            account_id = UUID(parts[2]) if parts[2] else None
        except ValueError:
            return None
        if purpose is not GooglePurpose.LOGIN and account_id is None:
            return None
        return cls(portal, parts[3], purpose, account_id)
