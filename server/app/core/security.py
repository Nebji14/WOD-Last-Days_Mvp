"""Vérification des jetons de session et gestion des cookies de session.

Les jetons Supabase ne sont jamais exposés au JavaScript du client : ils
voyagent dans des cookies ``HttpOnly``.
"""

import asyncio
import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import jwt
from fastapi import Response

from app.core.config import Settings

ACCESS_COOKIE = "hunter_at"
REFRESH_COOKIE = "hunter_rt"

_JWT_ALGORITHMS = ["ES256", "RS256"]
_JWT_AUDIENCE = "authenticated"
_JWKS_CACHE_SECONDS = 3600
# Tolérance sur les dates du jeton (émission, expiration) : l'horloge de
# Supabase peut avancer de quelques fractions de seconde sur celle du serveur,
# ce qui ferait refuser un jeton tout juste émis.
_JWT_CLOCK_LEEWAY_SECONDS = 5


# Longueur du vérificateur PKCE : 64 octets aléatoires donnent 86 caractères,
# dans la plage de 43 à 128 imposée par OAuth.
_PKCE_VERIFIER_BYTES = 64


class InvalidTokenError(Exception):
    """Le jeton est absent, mal signé, expiré ou destiné à un autre service."""


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Informations vérifiées extraites d'un jeton d'accès.

    Attributs:
        expires_at: date d'expiration du jeton, en secondes depuis l'époque Unix.
    """

    account_id: UUID
    expires_at: float


@dataclass(frozen=True, slots=True)
class SessionTokens:
    """Jetons d'une session ouverte auprès du fournisseur d'identité."""

    access_token: str
    refresh_token: str
    expires_in: int


class TokenVerifier(Protocol):
    """Contrat de vérification d'un jeton d'accès."""

    async def verify(self, token: str) -> TokenClaims:
        """Retourne les informations du jeton ou lève ``InvalidTokenError``."""
        ...


class SupabaseTokenVerifier:
    """Vérifie les jetons Supabase à l'aide des clés publiques du projet (JWKS).

    Contrôle la signature, l'expiration, l'émetteur et l'audience.

    Args:
        supabase_url: adresse du projet Supabase.
    """

    def __init__(self, supabase_url: str) -> None:
        self._issuer = f"{supabase_url}/auth/v1"
        self._jwks = jwt.PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json",
            cache_keys=True,
            lifespan=_JWKS_CACHE_SECONDS,
        )

    async def verify(self, token: str) -> TokenClaims:
        """Vérifie un jeton d'accès.

        Raises:
            InvalidTokenError: si une vérification échoue.
        """
        try:
            # La récupération des clés est un appel réseau bloquant.
            signing_key = await asyncio.to_thread(self._jwks.get_signing_key_from_jwt, token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=_JWT_ALGORITHMS,
                audience=_JWT_AUDIENCE,
                issuer=self._issuer,
                leeway=_JWT_CLOCK_LEEWAY_SECONDS,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
            return TokenClaims(account_id=UUID(payload["sub"]), expires_at=float(payload["exp"]))
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            raise InvalidTokenError from exc


def set_session_cookies(response: Response, tokens: SessionTokens, settings: Settings) -> None:
    """Dépose les cookies de session.

    Le cookie de rafraîchissement vit ``session_idle_seconds`` et il est
    renouvelé à chaque rafraîchissement : la session expire donc après cette
    durée d'inactivité.
    """
    common = {"httponly": True, "secure": settings.is_production, "samesite": "lax", "path": "/"}
    response.set_cookie(ACCESS_COOKIE, tokens.access_token, max_age=tokens.expires_in, **common)  # type: ignore[arg-type]
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=settings.session_idle_seconds,
        **common,  # type: ignore[arg-type]
    )


def clear_session_cookies(response: Response, settings: Settings) -> None:
    """Supprime les cookies de session du navigateur."""
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            name, path="/", httponly=True, secure=settings.is_production, samesite="lax"
        )


def new_pkce_verifier() -> str:
    """Tire un secret à usage unique qui lie la connexion externe à ce navigateur."""
    return secrets.token_urlsafe(_PKCE_VERIFIER_BYTES)


def pkce_challenge(verifier: str) -> str:
    """Empreinte SHA-256 du vérificateur, envoyée au fournisseur au départ de la connexion."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
