"""Règles métier des comptes : rôles, nom d'utilisateur, mot de passe.

Module pur : aucun accès réseau ni base de données.
"""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 24
_USERNAME_PATTERN = re.compile(r"[A-Za-z0-9._-]{3,24}")

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
    """

    id: UUID
    username: str
    display_name: str
    auth_email: str
    role: Role
    status: AccountStatus

    @property
    def is_active(self) -> bool:
        """Un compte désactivé ne peut plus ouvrir ni poursuivre de session."""
        return self.status is AccountStatus.ACTIVE


def is_valid_username(username: str) -> bool:
    """Vérifie le format d'un nom d'utilisateur.

    De 3 à 24 caractères parmi les lettres non accentuées, les chiffres, le
    point, le tiret et le tiret bas. Ce format garantit une adresse technique
    valide.
    """
    return _USERNAME_PATTERN.fullmatch(username) is not None


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


def technical_email(username: str, domain: str) -> str:
    """Construit l'adresse technique d'un joueur à partir de son nom d'utilisateur.

    Le fournisseur d'identité exige une adresse ; elle reste invisible pour le
    joueur. La casse est neutralisée pour rester cohérente avec
    l'unicité insensible à la casse du nom d'utilisateur.
    """
    return f"{username.lower()}@{domain}"
