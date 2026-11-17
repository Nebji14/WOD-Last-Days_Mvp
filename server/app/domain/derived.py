"""Valeurs de base calculées d'une feuille.

Une valeur de base est une référence : elle est recalculée à chaque lecture et
n'est jamais stockée. La valeur effective, saisie par le joueur ou le MJ, est
la seule conservée ; un recalcul ne la modifie jamais.

Module pur : aucun accès réseau ni base de données.
"""

from collections.abc import Mapping
from dataclasses import dataclass

BASE_SIZE = 5
_SPEED_BONUS = 5


@dataclass(frozen=True, slots=True)
class BaseValues:
    """Valeurs de base d'une feuille."""

    size: int
    speed: int
    defense: int
    initiative: int
    health: int
    willpower: int


def base_values(traits: Mapping[str, int], effective_size: int) -> BaseValues:
    """Calcule les valeurs de base à partir des attributs et compétences.

    Args:
        traits: valeurs des attributs et compétences de la feuille.
        effective_size: Taille effective saisie ; la santé de base en dépend
           .

    Returns:
        Taille = 5 ; Vitesse = Force + Dextérité + 5 ; Défense = min(Astuce,
        Dextérité) + Sports ; Initiative = Dextérité + Calme ;
        Santé = Taille effective + Vigueur ; Volonté = Résolution +
        Calme.
    """
    return BaseValues(
        size=BASE_SIZE,
        speed=traits["strength"] + traits["dexterity"] + _SPEED_BONUS,
        defense=min(traits["wits"], traits["dexterity"]) + traits["athletics"],
        initiative=traits["dexterity"] + traits["composure"],
        health=effective_size + traits["stamina"],
        willpower=traits["resolve"] + traits["composure"],
    )
