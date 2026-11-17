"""Tests de la vérification des jetons d'accès Supabase.

Les clés publiques du projet sont remplacées par une clé générée pour le test :
aucun appel réseau.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.security import InvalidTokenError, SupabaseTokenVerifier, TokenClaims

SUPABASE_URL = "https://exemple.supabase.co"
ISSUER = f"{SUPABASE_URL}/auth/v1"
PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


@dataclass
class _SigningKey:
    key: Any


class _StaticKeys:
    """Remplace le client JWKS : renvoie toujours la clé publique du test."""

    def get_signing_key_from_jwt(self, token: str) -> _SigningKey:
        return _SigningKey(PRIVATE_KEY.public_key())


def _verifier() -> SupabaseTokenVerifier:
    verifier = SupabaseTokenVerifier(SUPABASE_URL)
    verifier._jwks = _StaticKeys()  # type: ignore[assignment]
    return verifier


def _verify(token: str) -> TokenClaims:
    return asyncio.run(_verifier().verify(token))


def _token(issued_offset: float = 0, expires_offset: float = 3600) -> str:
    now = time.time()
    claims = {
        "sub": str(uuid4()),
        "aud": "authenticated",
        "iss": ISSUER,
        "iat": int(now + issued_offset),
        "exp": int(now + expires_offset),
    }
    return jwt.encode(claims, PRIVATE_KEY, algorithm="ES256")


def test_accepts_a_valid_token() -> None:
    claims = _verify(_token())
    assert claims.expires_at > time.time()


def test_accepts_a_token_issued_slightly_in_the_future() -> None:
    """Horloge de Supabase en avance d'une ou deux secondes : le jeton reste valide."""
    _verify(_token(issued_offset=2))


def test_rejects_a_token_issued_well_in_the_future() -> None:
    with pytest.raises(InvalidTokenError):
        _verify(_token(issued_offset=120))


def test_rejects_an_expired_token() -> None:
    with pytest.raises(InvalidTokenError):
        _verify(_token(issued_offset=-3700, expires_offset=-60))
