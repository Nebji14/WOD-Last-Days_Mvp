"""Jets de dés des Chroniques des Ténèbres.

On lance une réserve de d10. Un dé réussit sur 8, 9 ou 10, et un dé égal ou
supérieur au seuil de relance (10, ou 9 et 8 avec les options) se relance.
Une réserve vide devient un dé de chance : seul un 10 réussit, et un 1 est un
échec dramatique. Cinq réussites ou plus font une réussite exceptionnelle.

Module pur : aucun accès réseau ni base de données. Le hasard est fourni par
l'appelant.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.domain.accounts import Role
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES, SKILLS, Category

DIE_FACES = 10
SUCCESS_THRESHOLD = 8
EXCEPTIONAL_SUCCESSES = 5
SPECIALTY_BONUS = 1
WILLPOWER_BONUS = 3
MODIFIER_MIN = -10
MODIFIER_MAX = 5
FREE_POOL_MAX = 30
# Compétence à 0 : malus selon sa catégorie.
UNSKILLED_PENALTY = {Category.MENTAL: -3, Category.PHYSICAL: -1, Category.SOCIAL: -1}
NPC_TRAITS = ("power", "finesse", "resilience")

# Tire un dé : retourne une face de 1 à 10.
DieRoller = Callable[[], int]


class RollKind(StrEnum):
    """Nature du jet."""

    POOL = "pool"  # attribut + compétence
    INITIATIVE = "initiative"  # initiative + 1 dé
    CONSCIOUSNESS = "consciousness"  # Vigueur, pour rester conscient
    TRAIT = "trait"  # Puissance, Finesse ou Résilience d'un PNJ simplifié
    FREE = "free"  # réserve libre du MJ


class Outcome(StrEnum):
    """Issue d'un jet de réussites."""

    DRAMATIC_FAILURE = "dramatic_failure"
    FAILURE = "failure"
    SUCCESS = "success"
    EXCEPTIONAL = "exceptional"


class DiceRuleError(Exception):
    """La demande de jet est incohérente (trait inconnu, option interdite…)."""


@dataclass(frozen=True, slots=True)
class PoolPart:
    """Élément de la réserve : ``key`` est un trait ou un bonus, ``value`` son apport."""

    key: str
    value: int


@dataclass(frozen=True, slots=True)
class PoolOptions:
    """Options choisies avant le jet."""

    specialty: bool = False
    willpower: bool = False
    modifier: int = 0
    again: int = 10
    rote: bool = False


def check_options(options: PoolOptions) -> None:
    """Refuse un seuil de relance ou un modificateur hors des bornes.

    Raises:
        DiceRuleError: pour une option invalide.
    """
    if options.again not in (8, 9, 10):
        raise DiceRuleError("again")
    if not MODIFIER_MIN <= options.modifier <= MODIFIER_MAX:
        raise DiceRuleError("modifier")


def skill_category(skill: str) -> Category:
    """Catégorie d'une compétence."""
    return next(category for category, names in SKILLS.items() if skill in names)


def pool_parts(
    traits: dict[str, int],
    attribute: str,
    second: str | None,
    has_specialty: bool,
    options: PoolOptions,
    wound_penalty: int,
) -> list[PoolPart]:
    """Compose la réserve d'un jet : un attribut, plus une compétence ou un second attribut.

    Une compétence à 0 donne son malus de catégorie ; la spécialité ne vaut
    que pour une compétence qui en porte une.

    Args:
        traits: valeurs des attributs et compétences de la feuille.
        has_specialty: la compétence choisie porte au moins une spécialité.
        wound_penalty: malus de blessure en cours (0 ou négatif).

    Raises:
        DiceRuleError: pour un trait inconnu, ou une spécialité impossible.
    """
    known = (*ATTRIBUTE_NAMES, *SKILL_NAMES)
    if attribute not in ATTRIBUTE_NAMES or (second is not None and second not in known):
        raise DiceRuleError("trait")
    parts = [PoolPart(attribute, traits[attribute])]
    is_skill = second in SKILL_NAMES
    if second is not None:
        parts.append(PoolPart(second, traits[second]))
        if is_skill and traits[second] == 0:
            parts.append(PoolPart("unskilled", UNSKILLED_PENALTY[skill_category(second)]))
    if options.specialty:
        if not (is_skill and has_specialty):
            raise DiceRuleError("specialty")
        parts.append(PoolPart("specialty", SPECIALTY_BONUS))
    return parts + bonus_parts(options, wound_penalty)


def bonus_parts(options: PoolOptions, wound_penalty: int) -> list[PoolPart]:
    """Volonté, malus de blessure et modificateur du MJ, quand ils comptent."""
    parts: list[PoolPart] = []
    if options.willpower:
        parts.append(PoolPart("willpower", WILLPOWER_BONUS))
    if wound_penalty:
        parts.append(PoolPart("wounds", wound_penalty))
    if options.modifier:
        parts.append(PoolPart("modifier", options.modifier))
    return parts


def pool_size(parts: list[PoolPart]) -> int:
    """Nombre de dés : la somme des éléments, 0 au minimum (dé de chance)."""
    return max(0, sum(part.value for part in parts))


def roll_dice(count: int, roll_die: DieRoller) -> list[int]:
    """Lance ``count`` dés."""
    return [roll_die() for _ in range(count)]


def is_success(face: int, chance: bool) -> bool:
    """Un dé réussit sur 8 et plus ; un dé de chance seulement sur 10."""
    return face == DIE_FACES if chance else face >= SUCCESS_THRESHOLD


def rerolls_after(faces: list[int], again: int, rote_applies: bool, chance: bool) -> int:
    """Nombre de dés à relancer après une vague.

    Les dés au seuil de relance repartent ; avec l'action assurée, les échecs
    de la première vague repartent aussi. Un dé de chance ne se relance que sur 10.
    """
    threshold = DIE_FACES if chance else again
    count = sum(1 for face in faces if face >= threshold)
    if rote_applies and not chance:
        count += sum(1 for face in faces if not is_success(face, chance))
    return count


def count_successes(stages: list[list[int]], chance: bool) -> int:
    """Total des réussites, relances comprises."""
    return sum(1 for faces in stages for face in faces if is_success(face, chance))


def outcome(stages: list[list[int]], chance: bool) -> Outcome:
    """Issue du jet : un 1 au premier dé de chance est un échec dramatique."""
    successes = count_successes(stages, chance)
    if chance and successes == 0 and stages and stages[0][:1] == [1]:
        return Outcome.DRAMATIC_FAILURE
    if successes == 0:
        return Outcome.FAILURE
    return Outcome.EXCEPTIONAL if successes >= EXCEPTIONAL_SUCCESSES else Outcome.SUCCESS


@dataclass(frozen=True, slots=True)
class DiceRoll:
    """Jet en cours ou terminé, rejoué à l'identique sur tous les écrans.

    Attributs:
        roller_name: nom du personnage, ou du compte pour un jet libre du MJ.
        parts: composition de la réserve, affichée telle quelle.
        chance: réserve vide, lancée comme un dé de chance.
        stages: faces de chaque vague : le premier lancer, puis les relances.
        pending: dés qui restent à relancer ; 0 quand le jet est terminé.
        base: initiative ajoutée au dé, pour un jet d'initiative.
        secret: jet du MJ, montré au MJ seul.
    """

    id: UUID
    roller_id: UUID
    roller_role: Role
    roller_name: str
    character_id: UUID | None
    kind: RollKind
    parts: list[PoolPart]
    chance: bool
    again: int
    rote: bool
    secret: bool
    stages: list[list[int]]
    pending: int
    base: int = 0

    @property
    def finished(self) -> bool:
        """Plus aucun dé à relancer."""
        return self.pending == 0

    @property
    def successes(self) -> int:
        """Réussites totales ; sans objet pour l'initiative."""
        return count_successes(self.stages, self.chance)

    @property
    def total(self) -> int | None:
        """Résultat d'initiative : la valeur plus le dé ; ``None`` pour les autres jets."""
        if self.kind is not RollKind.INITIATIVE:
            return None
        penalty = sum(part.value for part in self.parts if part.key == "wounds")
        return self.base + penalty + sum(self.stages[0])


def roll_detail(roll: DiceRoll) -> dict[str, Any]:
    """Détail d'un jet, prêt pour le JSON : rejoué à la table et gardé dans le chat.

    ``outcome`` reste ``None`` tant que le jet n'est pas terminé, et pour l'initiative.
    """
    finished_pool = roll.finished and roll.kind is not RollKind.INITIATIVE
    return {
        "id": str(roll.id),
        "roller_id": str(roll.roller_id),
        "roller_role": roll.roller_role.value,
        "roller_name": roll.roller_name,
        "character_id": None if roll.character_id is None else str(roll.character_id),
        "kind": roll.kind.value,
        "parts": [{"key": part.key, "value": part.value} for part in roll.parts],
        "chance": roll.chance,
        "again": roll.again,
        "rote": roll.rote,
        "secret": roll.secret,
        "stages": [list(faces) for faces in roll.stages],
        "pending": roll.pending,
        "successes": roll.successes,
        "outcome": outcome(roll.stages, roll.chance).value if finished_pool else None,
        "total": roll.total,
    }
