"""Profil d'une feuille de PNJ : modèle et données propres (RM-021, RM-022).

Module sans dépendance, lu par le modèle du personnage comme par les règles
des PNJ.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class NpcModel(StrEnum):
    """Modèle choisi à la création, définitif au MVP (RM-021, Q07-2)."""

    FULL = "full"
    SIMPLIFIED = "simplified"


@dataclass(frozen=True, slots=True)
class NpcProfile:
    """Données propres à une feuille de PNJ.

    Attributs:
        notes: notes intégrées, distinctes des notes autonomes (US-039 · CA7).
        power, finesse, resilience: de 1 à 10 pour le modèle simplifié,
            ``None`` pour le modèle complet (RM-022).
    """

    model: NpcModel
    category_id: UUID | None
    notes: str
    power: int | None
    finesse: int | None
    resilience: int | None

    @property
    def is_simplified(self) -> bool:
        return self.model is NpcModel.SIMPLIFIED
