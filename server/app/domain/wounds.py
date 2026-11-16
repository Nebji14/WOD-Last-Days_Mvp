"""Piste de blessures d'une feuille (RM-008, RM-009, RM-011).

La piste est une chaîne où chaque caractère est une blessure : ``*`` aggravée,
``X`` létale, ``/`` contondante (RM-009). Elle est toujours rangée par gravité
décroissante et sans trou ; les cases vides, à droite, ne sont pas stockées
(RM-008).

Module pur : aucun accès réseau ni base de données.
"""

from enum import StrEnum


class Wound(StrEnum):
    """Type de blessure et son symbole (RM-009)."""

    AGGRAVATED = "*"
    LETHAL = "X"
    BASHING = "/"


# Gravité décroissante : ordre de rangement de la piste (RM-008).
_SEVERITY_ORDER = (Wound.AGGRAVATED, Wound.LETHAL, Wound.BASHING)
_NEXT_SEVERITY = {Wound.BASHING: Wound.LETHAL, Wound.LETHAL: Wound.AGGRAVATED}


class WoundRuleError(Exception):
    """L'opération demandée laisserait la piste dans un état interdit."""


class TrackFullError(WoundRuleError):
    """Toutes les cases de santé portent déjà une blessure (RM-011)."""


class NoSuchWoundError(WoundRuleError):
    """La piste ne contient aucune blessure du type demandé."""


def _sorted(wounds: str) -> str:
    return "".join(symbol * wounds.count(symbol) for symbol in _SEVERITY_ORDER)


def is_valid_track(track: str, capacity: int) -> bool:
    """Vérifie qu'une piste respecte RM-008 et RM-011.

    Args:
        track: piste à contrôler.
        capacity: santé maximale effective, c'est-à-dire le nombre de cases.
    """
    known = all(symbol in Wound for symbol in track)
    return known and track == _sorted(track) and len(track) <= capacity


def add_wound(track: str, wound: Wound, capacity: int) -> str:
    """Ajoute une blessure en gardant la piste rangée (RM-008).

    Aucune blessure existante n'est effacée pour faire de la place.

    Raises:
        TrackFullError: si la piste est pleine (RM-011).
    """
    if len(track) >= capacity:
        raise TrackFullError
    return _sorted(track + wound)


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
    """Aggrave une blessure d'un cran : contondante → létale → aggravée (RM-009).

    Raises:
        NoSuchWoundError: si la piste ne contient pas ce type de blessure, ou
            si la blessure est déjà aggravée.
    """
    worse = _NEXT_SEVERITY.get(wound)
    if worse is None or wound not in track:
        raise NoSuchWoundError
    return _sorted(track.replace(wound, worse, 1))
