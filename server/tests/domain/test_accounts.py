"""Règles des comptes : nom d'utilisateur, mot de passe, adresse technique."""

import pytest

from app.domain.accounts import (
    PasswordRule,
    is_valid_username,
    numbered_username,
    password_violations,
    technical_email,
    username_from_identity,
)


@pytest.mark.parametrize("username", ["lea", "lea.vale", "Yanis_42", "a-b-c", "x" * 24])
def test_valid_usernames(username: str) -> None:
    assert is_valid_username(username)


@pytest.mark.parametrize(
    "username", ["", "ab", "x" * 25, "léa", "lea vale", "lea@vale", "lea/vale", "lea\n"]
)
def test_invalid_usernames(username: str) -> None:
    assert not is_valid_username(username)


def test_compliant_password_has_no_violation() -> None:
    assert password_violations("chasseur-2026") == []


@pytest.mark.parametrize(
    ("password", "rule"),
    [
        ("court1abc", PasswordRule.MIN_LENGTH),
        ("1234567890", PasswordRule.LETTER),
        ("sanschiffre", PasswordRule.DIGIT),
        ("a1" + "x" * 71, PasswordRule.MAX_LENGTH),
    ],
)
def test_password_violations(password: str, rule: PasswordRule) -> None:
    assert rule in password_violations(password)


def test_password_max_length_counts_bytes() -> None:
    assert PasswordRule.MAX_LENGTH in password_violations("é" * 36 + "a1")


def test_technical_email_ignores_case() -> None:
    assert technical_email("Lea.Vale", "users.hunter.local") == "lea.vale@users.hunter.local"


# --- Nom d'utilisateur d'un compte Google ------------------------------------------------


@pytest.mark.parametrize(
    ("full_name", "email", "expected"),
    [
        ("Léa Vale", "x@gmail.com", "Lea.Vale"),
        ("  Jean-Éric  d'Arc ", "x@gmail.com", "Jean-Eric.dArc"),
        (None, "lea.vale+jdr@gmail.com", "lea.valejdr"),
        ("李", "zo@gmail.com", "chasseur"),
        ("Un nom vraiment beaucoup trop long", "x@gmail.com", "Un.nom.vraiment.beau"),
    ],
)
def test_username_from_identity_is_always_valid(
    full_name: str | None, email: str, expected: str
) -> None:
    username = username_from_identity(full_name, email)

    assert username == expected
    assert is_valid_username(numbered_username(username, 999))


def test_numbered_username_keeps_first_name_unchanged() -> None:
    assert numbered_username("lea", 1) == "lea"
    assert numbered_username("lea", 2) == "lea2"
