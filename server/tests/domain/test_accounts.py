"""Règles des comptes : noms, mot de passe, adresse technique."""

from uuid import UUID

import pytest

from app.domain.accounts import (
    PasswordRule,
    is_valid_username,
    normalized_display_name,
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


def test_technical_email_does_not_depend_on_username() -> None:
    identifier = UUID("00000000-0000-0000-0000-00000000000a")

    assert technical_email(identifier, "users.hunter.local") == (
        "0000000000000000000000000000000a@users.hunter.local"
    )


# --- Nom affiché --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Léa", "Léa"),
        ("  Léa   la  Chasseuse ", "Léa la Chasseuse"),
        ("x" * 40, "x" * 40),
        ("Le\u0301a", "Léa"),
    ],
)
def test_display_name_is_normalized(name: str, expected: str) -> None:
    assert normalized_display_name(name) == expected


@pytest.mark.parametrize("name", ["", "   ", "x" * 41, "Lé\u200ba", "Léa\x00", "\u202eaéL"])
def test_invalid_display_names(name: str) -> None:
    assert normalized_display_name(name) is None


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
