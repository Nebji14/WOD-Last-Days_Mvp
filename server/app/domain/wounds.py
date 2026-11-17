"""Piste de blessures d'une feuille.

La piste est une chaîne où chaque caractère est une blessure : ``*`` aggravée,
``X`` létale, ``/`` contondante. Elle est toujours rangée par gravité
décroissante et sans trou ; les cases vides, à droite, ne sont pas stockées.
Quand toutes les cases sont prises, une nouvelle blessure aggrave la moins
grave au lieu d'en effacer une.

Module pur : aucun accès réseau ni base de données.
"""

from enum import StrEnum


class Wound(StrEnum):
    """Type de blessure et son symbole."""

    AGGRAVATED = "*"
    LETHAL = "X"
    BASHING = "/"


# Gravité décroissante : ordre de rangement de la piste.
_SEVERITY_ORDER = (Wound.AGGRAVATED, Wound.LETHAL, Wound.BASHING)
_NEXT_SEVERITY = {Wound.BASHING: Wound.LETHAL, Wound.LETHAL: Wound.AGGRAVATED}


class WoundRuleError(Exception):
    """L'opération demandée laisserait la piste dans un état interdit."""


class TrackFullError(WoundRuleError):
    """Toutes les cases portent une blessure aggravée : le personnage est mort."""


class NoSuchWoundError(WoundRuleError):
    """La piste ne contient aucune blessure du type demandé."""


def _sorted(wounds: str) -> str:
    return "".join(symbol * wounds.count(symbol) for symbol in _SEVERITY_ORDER)


def is_valid_track(track: str, capacity: int) -> bool:
    """Vérifie qu'une piste est rangée par gravité et ne dépasse pas la santé maximale.

    Args:
        track: piste à contrôler.
        capacity: santé maximale effective, c'est-à-dire le nombre de cases.
    """
    known = all(symbol in Wound for symbol in track)
    return known and track == _sorted(track) and len(track) <= capacity


def add_wound(track: str, wound: Wound, capacity: int) -> str:
    """Ajoute une blessure en gardant la piste rangée.

    S'il reste une case vide, la blessure s'y inscrit et décale les moins
    graves vers la droite. Sinon, elle aggrave la blessure la moins grave :
    contondante → létale, létale → aggravée ; une blessure aggravée la rend
    directement aggravée. Aucune blessure n'est effacée.

    Raises:
        TrackFullError: si toutes les cases sont déjà aggravées.
    """
    if len(track) < capacity:
        return _sorted(track + wound)
    least = Wound(track[-1]) if track else None
    if least is None or least is Wound.AGGRAVATED:
        raise TrackFullError
    worse = Wound.AGGRAVATED if wound is Wound.AGGRAVATED else _NEXT_SEVERITY[least]
    return _sorted(track[:-1] + worse)


def heal_wound(track: str, wound: Wound | None = None) -> str:
    """Retire une blessure.

    Args:
        track: piste actuelle.
        wound: type à retirer ; par défaut, la blessure la moins grave.

    Raises:
        NoSuchWoundError: si la piste est vide ou sans blessure de ce type.
    """
    target = wound.value if wound is not None else track[-1:]
    if not target or target not in track:
        raise NoSuchWoundError
    return _sorted(track.replace(target, "", 1))


def worsen_wound(track: str, wound: Wound) -> str:
    """Aggrave une blessure d'un cran : contondante → létale → aggravée.

    Raises:
        NoSuchWoundError: si la piste ne contient pas ce type de blessure, ou
            si la blessure est déjà aggravée.
    """
    worse = _NEXT_SEVERITY.get(wound)
    if worse is None or wound not in track:
        raise NoSuchWoundError
    return _sorted(track.replace(wound, worse, 1))
