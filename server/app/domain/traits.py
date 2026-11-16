"""Attributs et compétences d'une feuille de personnage (MCD 2.5).

Module pur : aucun accès réseau ni base de données. Les identifiants sont ceux
des colonnes de la table ``character_sheet``.
"""

from enum import StrEnum


class Category(StrEnum):
    """Catégorie d'attributs ou de compétences."""

    MENTAL = "mental"
    PHYSICAL = "physical"
    SOCIAL = "social"


# Attributs : intelligence, astuce, résolution / force, dextérité, vigueur /
# présence, manipulation, calme.
ATTRIBUTES: dict[Category, tuple[str, ...]] = {
    Category.MENTAL: ("intelligence", "wits", "resolve"),
    Category.PHYSICAL: ("strength", "dexterity", "stamina"),
    Category.SOCIAL: ("presence", "manipulation", "composure"),
}

# Compétences, dans l'ordre du MLD (enum competence_feuille) : érudition,
# informatique, artisanat, investigation, médecine, occultisme, politique,
# sciences / sports, bagarre, conduite, armes à feu, larcin, discrétion, survie,
# armes blanches / animaux, empathie, expression, intimidation, persuasion,
# entregent, expérience de la rue, subterfuge.
SKILLS: dict[Category, tuple[str, ...]] = {
    Category.MENTAL: (
        "academics",
        "computer",
        "crafts",
        "investigation",
        "medicine",
        "occult",
        "politics",
        "science",
    ),
    Category.PHYSICAL: (
        "athletics",
        "brawl",
        "drive",
        "firearms",
        "larceny",
        "stealth",
        "survival",
        "weaponry",
    ),
    Category.SOCIAL: (
        "animal_ken",
        "empathy",
        "expression",
        "intimidation",
        "persuasion",
        "socialize",
        "streetwise",
        "subterfuge",
    ),
}

ATTRIBUTE_NAMES: tuple[str, ...] = tuple(name for names in ATTRIBUTES.values() for name in names)
SKILL_NAMES: tuple[str, ...] = tuple(name for names in SKILLS.values() for name in names)

ATTRIBUTE_MIN = 1
# Plafond ordinaire des attributs ; l'éveil le porte à ``ATTRIBUTE_MAX_AWAKENED``
# (maquette 05, ÉVEIL V1 et V2).
ATTRIBUTE_MAX = 5
ATTRIBUTE_MAX_AWAKENED = 10
SKILL_MIN = 0
SKILL_MAX = 5

SPECIALTY_MAX_LENGTH = 100


def attribute_max(awakened: bool) -> int:
    """Plafond d'un attribut selon que le personnage est éveillé ou non."""
    return ATTRIBUTE_MAX_AWAKENED if awakened else ATTRIBUTE_MAX


def parse_specialties(text: str) -> list[str]:
    """Découpe le champ de spécialités d'une compétence (maquette 05, I9).

    Les spécialités sont séparées par des virgules. Les espaces autour de
    chacune sont retirés, les entrées vides et les doublons (casse ignorée)
    sont écartés. Un champ vide ne donne aucune spécialité.
    """
    seen: set[str] = set()
    labels: list[str] = []
    for part in text.split(","):
        label = " ".join(part.split())
        if label and label.lower() not in seen:
            seen.add(label.lower())
            labels.append(label)
    return labels
