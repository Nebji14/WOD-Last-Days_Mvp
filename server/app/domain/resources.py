"""Ressources libres d'un personnage (Mana, Douleur…).

Une ressource fonctionne comme la Volonté, sans base calculée : un maximum
saisi à la main et une valeur disponible, comprise entre 0 et ce maximum, qui
baisse quand un pouvoir la dépense. Elle est commune à toutes les formes.

Module pur : aucun accès réseau ni base de données.
"""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

NAME_MAX_LENGTH = 40
VALUE_MAX = 30
RESOURCES_MAX = 10


class ResourceField(StrEnum):
    """Champ modifiable d'une ressource."""

    NAME = "name"
    MAX = "max_value"
    CURRENT = "current_value"


class ResourceRuleError(Exception):
    """Saisie contraire aux règles d'une ressource ; le message nomme la règle."""


@dataclass(frozen=True, slots=True)
class Resource:
    """Ressource d'un personnage."""

    id: UUID
    name: str
    max_value: int
    current_value: int


def clean_name(name: str, others: list[Resource]) -> str:
    """Nom nettoyé, refusé s'il est vide, trop long ou déjà pris.

    Args:
        others: autres ressources du personnage ; la comparaison ignore la casse.

    Raises:
        ResourceRuleError: ``resource_name`` ou ``resource_name_taken``.
    """
    cleaned = name.strip()
    if not 1 <= len(cleaned) <= NAME_MAX_LENGTH:
        raise ResourceRuleError("resource_name")
    if any(other.name.lower() == cleaned.lower() for other in others):
        raise ResourceRuleError("resource_name_taken")
    return cleaned


def check_max(value: int) -> None:
    """Le maximum va de 0 à 30, comme celui de la Volonté.

    Raises:
        ResourceRuleError: ``resource_max``.
    """
    if not 0 <= value <= VALUE_MAX:
        raise ResourceRuleError("resource_max")


def check_current(value: int, maximum: int) -> None:
    """La valeur disponible reste entre 0 et le maximum.

    Raises:
        ResourceRuleError: ``resource_above_max``.
    """
    if not 0 <= value <= maximum:
        raise ResourceRuleError("resource_above_max")


def check_count(existing: int) -> None:
    """Un personnage porte au plus dix ressources.

    Raises:
        ResourceRuleError: ``resource_count``.
    """
    if existing >= RESOURCES_MAX:
        raise ResourceRuleError("resource_count")
