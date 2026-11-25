"""Règles métier des comptes : rôles, nom d'utilisateur, mot de passe.

Module pur : aucun accès réseau ni base de données.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 24
_USERNAME_PATTERN = re.compile(r"[A-Za-z0-9._-]{3,24}")
_USERNAME_FORBIDDEN = re.compile(r"[^A-Za-z0-9._-]+")
# Place laissée en fin de nom pour un numéro quand le nom proposé est déjà pris.
_NUMBER_ROOM = 4
_FALLBACK_USERNAME = "chasseur"

DISPLAY_NAME_MAX_LENGTH = 40

PASSWORD_MIN_LENGTH = 10
# bcrypt, utilisé par le fournisseur d'identité, ignore les octets au-delà de 72.
PASSWORD_MAX_BYTES = 72


class Role(StrEnum):
    """Rôle d'un compte : joueur ou MJ (un seul compte MJ)."""

    PLAYER = "player"
    GM = "gm"


class AccountStatus(StrEnum):
    """État d'un compte : actif ou désactivé."""

    ACTIVE = "active"
    DISABLED = "disabled"


class PasswordRule(StrEnum):
    """Règles de sécurité d'un mot de passe."""

    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    LETTER = "letter"
    DIGIT = "digit"


@dataclass(frozen=True, slots=True)
class Account:
    """Compte joueur ou MJ.

    Attributs:
        auth_email: adresse connue du fournisseur d'identité. Donnée interne,
            jamais renvoyée au client.
        portrait: nom du fichier de la photo du compte (MJ), ``None`` sans photo.
    """

    id: UUID
    username: str
    display_name: str
    auth_email: str
    role: Role
    status: AccountStatus
    portrait: str | None = None

    @property
    def is_active(self) -> bool:
        """Un compte désactivé ne peut plus ouvrir ni poursuivre de session."""
        return self.status is AccountStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class LoginMethods:
    """Méthodes de connexion utilisables d'un compte."""

    password: bool
    google: bool


def is_valid_username(username: str) -> bool:
    """Vérifie le format d'un nom d'utilisateur.

    De 3 à 24 caractères parmi les lettres non accentuées, les chiffres, le
    point, le tiret et le tiret bas. Ce format garantit une adresse technique
    valide.
    """
    return _USERNAME_PATTERN.fullmatch(username) is not None


def normalized_display_name(name: str) -> str | None:
    """Nom affiché sans espace superflu, ou ``None`` s'il n'est pas valide.

    De 1 à 40 caractères visibles ; les caractères de contrôle ou invisibles sont
    refusés, car ils permettraient d'imiter le nom d'un autre.
    """
    normalized = " ".join(unicodedata.normalize("NFC", name).split())
    if not 1 <= len(normalized) <= DISPLAY_NAME_MAX_LENGTH:
        return None
    if any(unicodedata.category(char).startswith("C") for char in normalized):
        return None
    return normalized


def password_violations(password: str) -> list[PasswordRule]:
    """Liste les règles de sécurité non respectées par un mot de passe.

    Returns:
        Une liste vide si le mot de passe est conforme.
    """
    violations: list[PasswordRule] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        violations.append(PasswordRule.MIN_LENGTH)
    if len(password.encode("utf-8")) > PASSWORD_MAX_BYTES:
        violations.append(PasswordRule.MAX_LENGTH)
    if not any(char.isalpha() for char in password):
        violations.append(PasswordRule.LETTER)
    if not any(char.isdigit() for char in password):
        violations.append(PasswordRule.DIGIT)
    return violations


def technical_email(identifier: UUID, domain: str) -> str:
    """Construit l'adresse technique d'un joueur, exigée par le fournisseur d'identité.

    Invisible pour le joueur, elle ne dépend pas de son nom d'utilisateur : il
    peut en changer, et un autre joueur peut reprendre l'ancien.
    """
    return f"{identifier.hex}@{domain}"


def username_from_identity(full_name: str | None, email: str) -> str:
    """Propose un nom d'utilisateur valide pour un compte créé avec Google.

    Part du nom du compte Google, sinon de la partie de l'adresse avant « @ » :
    accents retirés, espaces remplacés par des points, autres caractères
    interdits supprimés. Le nom est raccourci pour laisser la place d'un numéro.
    """
    for source in (full_name or "", email.split("@", 1)[0]):
        ascii_text = unicodedata.normalize("NFKD", source).encode("ascii", "ignore").decode()
        dotted = re.sub(r"\s+", ".", ascii_text.strip())
        candidate = _USERNAME_FORBIDDEN.sub("", dotted).strip("._-")
        candidate = candidate[: USERNAME_MAX_LENGTH - _NUMBER_ROOM]
        if len(candidate) >= USERNAME_MIN_LENGTH:
            return candidate
    return _FALLBACK_USERNAME


def numbered_username(base: str, number: int) -> str:
    """Variante d'un nom déjà pris : ``lea`` puis ``lea2``, ``lea3``…"""
    return base if number <= 1 else f"{base}{number}"
