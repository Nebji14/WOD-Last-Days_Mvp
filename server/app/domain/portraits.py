"""Règles des portraits : l'image d'une forme de personnage.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from uuid import UUID

from app.domain.accounts import Account
from app.domain.character import can_edit, can_read

MAX_PORTRAIT_BYTES = 2 * 1024 * 1024
"""Poids maximal d'un portrait ; le client le réduit avant l'envoi."""

MAX_ORIGINAL_BYTES = 4 * 1024 * 1024
"""Poids maximal de la photo entière, gardée pour recadrer."""

PORTRAIT_NAME_PATTERN = r"^[0-9a-f]{32}\.(png|jpg|webp|gif)$"


@dataclass(frozen=True, slots=True)
class PortraitOwner:
    """Forme à laquelle appartient un portrait.

    Attributs:
        owner_id: propriétaire du personnage ; ``None`` pour un PNJ.
        is_main: forme principale, la seule montrée sur un siège.
        is_played: personnage joué à la table.
    """

    owner_id: UUID | None
    is_main: bool
    is_played: bool


def can_see_portrait(actor: Account, portrait: PortraitOwner) -> bool:
    """Le portrait affiché sur un siège est vu de tous, les autres par qui lit la fiche.

    Une forme alternative reste ainsi secrète pour les autres joueurs.
    """
    on_seat = portrait.is_main and portrait.is_played
    return on_seat or can_read(actor, portrait.owner_id)


def can_reframe_portrait(actor: Account, portrait: PortraitOwner) -> bool:
    """Seul qui modifie la fiche lit ou remplace la photo entière.

    Elle montre plus que le portrait cadré : les autres joueurs ne la voient jamais.
    """
    return can_edit(actor, portrait.owner_id)


def original_path(name: str) -> str:
    """Emplacement de la photo entière d'un portrait, dans le même bucket."""
    return f"originals/{name}"
