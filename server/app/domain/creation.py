"""Règles de création d'un personnage joueur.

Module pur : aucun accès réseau ni base de données.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from app.domain.traits import (
    ATTRIBUTE_MAX,
    ATTRIBUTE_MIN,
    ATTRIBUTES,
    SKILL_MAX,
    SKILL_MIN,
    SKILL_NAMES,
    SKILLS,
    SPECIALTY_MAX_LENGTH,
    Category,
)

# Points à répartir selon le rang de priorité de la catégorie (1re, 2e, 3e).
ATTRIBUTE_BUDGETS = {1: 5, 2: 4, 3: 3}
SKILL_BUDGETS = {1: 11, 2: 7, 3: 4}
SPECIALTY_COUNT = 3
# Une valeur d'attribut à partir de ce seuil se discute avec le MJ (alerte non bloquante).
ATTRIBUTE_ALERT_THRESHOLD = 4


class CreationRule(StrEnum):
    """Règle de création non respectée."""

    PRIORITIES = "priorities"
    ATTRIBUTE_RANGE = "attribute_range"
    ATTRIBUTE_BUDGET = "attribute_budget"
    SKILL_RANGE = "skill_range"
    SKILL_BUDGET = "skill_budget"
    SPECIALTY_COUNT = "specialty_count"
    SPECIALTY_TEXT = "specialty_text"
    SPECIALTY_SKILL = "specialty_skill"


@dataclass(frozen=True, slots=True)
class Violation:
    """Écart à une règle de création.

    Attributs:
        rule: règle en cause.
        subject: catégorie, attribut ou compétence concerné, ``None`` si
            l'écart est global.
    """

    rule: CreationRule
    subject: str | None = None


@dataclass(frozen=True, slots=True)
class Specialty:
    """Spécialité choisie à la création : une compétence et un texte libre."""

    skill: str
    label: str


Priorities = Mapping[Category, int]


def _valid_priorities(priorities: Priorities) -> bool:
    """Les trois catégories reçoivent les rangs 1, 2 et 3, chacun une fois."""
    return set(priorities) == set(Category) and sorted(priorities.values()) == [1, 2, 3]


def attribute_violations(priorities: Priorities, values: Mapping[str, int]) -> list[Violation]:
    """Contrôle la répartition des attributs.

    Chaque attribut a un point gratuit. S'y ajoutent exactement 5, 4 et 3
    points dans les catégories classées 1re, 2e et 3e. Un attribut reste
    compris entre 1 et 5.
    """
    if not _valid_priorities(priorities):
        return [Violation(CreationRule.PRIORITIES, "attributes")]
    violations: list[Violation] = []
    for category, names in ATTRIBUTES.items():
        out_of_range = [n for n in names if not ATTRIBUTE_MIN <= values[n] <= ATTRIBUTE_MAX]
        violations += [Violation(CreationRule.ATTRIBUTE_RANGE, name) for name in out_of_range]
        spent = sum(values[name] - ATTRIBUTE_MIN for name in names)
        if spent != ATTRIBUTE_BUDGETS[priorities[category]]:
            violations.append(Violation(CreationRule.ATTRIBUTE_BUDGET, category.value))
    return violations


def skill_violations(priorities: Priorities, values: Mapping[str, int]) -> list[Violation]:
    """Contrôle la répartition des compétences.

    Exactement 11, 7 et 4 points dans les catégories classées 1re, 2e et 3e,
    sans point gratuit. Ce classement est indépendant de celui des attributs.
    """
    if not _valid_priorities(priorities):
        return [Violation(CreationRule.PRIORITIES, "skills")]
    violations: list[Violation] = []
    for category, names in SKILLS.items():
        out_of_range = [n for n in names if not SKILL_MIN <= values[n] <= SKILL_MAX]
        violations += [Violation(CreationRule.SKILL_RANGE, name) for name in out_of_range]
        if sum(values[name] for name in names) != SKILL_BUDGETS[priorities[category]]:
            violations.append(Violation(CreationRule.SKILL_BUDGET, category.value))
    return violations


def specialty_violations(
    specialties: list[Specialty], skill_values: Mapping[str, int]
) -> list[Violation]:
    """Contrôle les spécialités.

    Exactement trois spécialités, chacune avec un texte non vide et portant
    sur une compétence dotée d'au moins un point.
    """
    violations: list[Violation] = []
    if len(specialties) != SPECIALTY_COUNT:
        violations.append(Violation(CreationRule.SPECIALTY_COUNT))
    for specialty in specialties:
        label = specialty.label.strip()
        if not label or len(label) > SPECIALTY_MAX_LENGTH or "," in label:
            violations.append(Violation(CreationRule.SPECIALTY_TEXT, specialty.skill))
        if specialty.skill not in SKILL_NAMES or skill_values.get(specialty.skill, 0) < 1:
            violations.append(Violation(CreationRule.SPECIALTY_SKILL, specialty.skill))
    return violations


def attributes_to_discuss(values: Mapping[str, int]) -> list[str]:
    """Attributs à 4 ou 5, à discuter avec le MJ. Alerte non bloquante."""
    return [name for name, value in values.items() if value >= ATTRIBUTE_ALERT_THRESHOLD]
