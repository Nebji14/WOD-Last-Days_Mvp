"""Passerelle vers Supabase Auth (API REST GoTrue).

Seul module du serveur à connaître le protocole du fournisseur d'identité.
"""

import logging
from uuid import UUID

import httpx

from app.core.config import Settings
from app.core.security import SessionTokens

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10.0


class IdentityProviderError(Exception):
    """Le fournisseur d'identité est injoignable ou a répondu de façon inattendue."""


class InvalidCredentialsError(Exception):
    """Les identifiants ou le jeton de rafraîchissement sont refusés."""


class IdentityAlreadyExistsError(Exception):
    """Une identité existe déjà pour cette adresse."""


class SupabaseAuthGateway:
    """Client des opérations d'authentification de Supabase.

    Args:
        settings: configuration du serveur (adresse du projet et clés).
        client: client HTTP partagé, fermé par l'application à l'arrêt.
    """

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._base_url = f"{settings.supabase_url}/auth/v1"
        self._client = client
        self._public_headers = {"apikey": settings.supabase_publishable_key}
        secret = settings.supabase_secret_key.get_secret_value()
        self._admin_headers = {"apikey": secret, "Authorization": f"Bearer {secret}"}

    async def create_user(self, email: str, password: str) -> UUID:
        """Crée une identité déjà confirmée et retourne son identifiant.

        Raises:
            IdentityAlreadyExistsError: si l'adresse est déjà utilisée.
            IdentityProviderError: pour toute autre réponse en erreur.
        """
        response = await self._request(
            "POST",
            "/admin/users",
            headers=self._admin_headers,
            json={"email": email, "password": password, "email_confirm": True},
        )
        if response.status_code == 422 and "already" in response.text.lower():
            raise IdentityAlreadyExistsError
        self._raise_for_unexpected(response)
        return UUID(response.json()["id"])

    async def delete_user(self, user_id: UUID) -> None:
        """Supprime une identité (compensation d'une création de compte échouée)."""
        response = await self._request(
            "DELETE", f"/admin/users/{user_id}", headers=self._admin_headers
        )
        self._raise_for_unexpected(response)

    async def sign_in(self, email: str, password: str) -> SessionTokens:
        """Ouvre une session par adresse et mot de passe.

        Raises:
            InvalidCredentialsError: si les identifiants sont refusés.
        """
        response = await self._request(
            "POST",
            "/token",
            params={"grant_type": "password"},
            headers=self._public_headers,
            json={"email": email, "password": password},
        )
        return self._tokens_or_invalid(response)

    async def refresh(self, refresh_token: str) -> SessionTokens:
        """Renouvelle une session.

        Raises:
            InvalidCredentialsError: si le jeton de rafraîchissement est refusé.
        """
        response = await self._request(
            "POST",
            "/token",
            params={"grant_type": "refresh_token"},
            headers=self._public_headers,
            json={"refresh_token": refresh_token},
        )
        return self._tokens_or_invalid(response)

    async def sign_out(self, access_token: str) -> None:
        """Révoque la session associée au jeton d'accès.

        Un jeton déjà expiré ou révoqué n'est pas une erreur : la session est
        de toute façon terminée.
        """
        response = await self._request(
            "POST",
            "/logout",
            params={"scope": "local"},
            headers={**self._public_headers, "Authorization": f"Bearer {access_token}"},
        )
        if response.status_code not in (204, 401, 403, 404):
            self._raise_for_unexpected(response)

    async def _request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        """Exécute une requête et convertit les pannes réseau en erreur du domaine."""
        try:
            return await self._client.request(
                method,
                f"{self._base_url}{path}",
                timeout=_TIMEOUT_SECONDS,
                **kwargs,  # type: ignore[arg-type]
            )
        except httpx.HTTPError as exc:
            logger.error("Fournisseur d'identité injoignable", exc_info=exc)
            raise IdentityProviderError from exc

    def _tokens_or_invalid(self, response: httpx.Response) -> SessionTokens:
        """Extrait les jetons d'une réponse, ou signale des identifiants refusés.

        Seul le statut 400 correspond à des identifiants refusés. Un statut 401
        ou 403 signale une clé d'API invalide : c'est une erreur de
        configuration, traitée comme une panne du fournisseur.
        """
        if response.status_code == 400:
            raise InvalidCredentialsError
        self._raise_for_unexpected(response)
        body = response.json()
        return SessionTokens(
            access_token=body["access_token"],
            refresh_token=body["refresh_token"],
            expires_in=int(body["expires_in"]),
        )

    @staticmethod
    def _raise_for_unexpected(response: httpx.Response) -> None:
        """Journalise le statut (jamais le corps, qui peut contenir des jetons)."""
        if response.is_error:
            logger.error("Réponse inattendue du fournisseur d'identité : %s", response.status_code)
            raise IdentityProviderError
