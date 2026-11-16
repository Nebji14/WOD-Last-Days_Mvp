"""Aides de test : participants connectés agissant sur la même application."""

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from httpx import Response

from app.core.security import ACCESS_COOKIE
from tests.conftest import PASSWORD, TestContext

GM_PASSWORD = "conteur-secret-9"


@dataclass
class Actor:
    """Participant connecté. Ses requêtes portent son propre cookie de session."""

    ctx: TestContext
    account_id: UUID
    token: str

    def request(self, method: str, path: str, **kwargs: Any) -> Response:
        response: Response = self.ctx.client.request(
            method, path, headers={"Cookie": f"{ACCESS_COOKIE}={self.token}"}, **kwargs
        )
        return response

    def ticket(self) -> str:
        """Demande un ticket de connexion temps réel."""
        return str(self.request("POST", "/api/realtime/ticket").json()["ticket"])


def _login(ctx: TestContext, path: str, username: str, password: str) -> Actor:
    response = ctx.client.post(path, json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.cookies[ACCESS_COOKIE]
    # Le client de test est partagé : chaque participant fournit son cookie lui-même.
    ctx.client.cookies.clear()
    return Actor(ctx, UUID(response.json()["id"]), token)


def player(ctx: TestContext, username: str) -> Actor:
    """Crée un joueur et ouvre sa session.

    Le compte est créé par le service : la limite de débit de la route
    d'inscription ne borne pas le nombre de joueurs d'un test.
    """
    asyncio.run(ctx.auth_service.register_player(username, PASSWORD, PASSWORD))
    return _login(ctx, "/api/auth/login", username, PASSWORD)


def game_master(ctx: TestContext) -> Actor:
    """Crée le compte du MJ et ouvre sa session."""
    asyncio.run(ctx.auth_service.create_gm("conteur", "mj@example.org", GM_PASSWORD))
    return _login(ctx, "/api/auth/gm/login", "conteur", GM_PASSWORD)


def error_code(response: Response) -> str:
    """Code d'erreur applicatif d'une réponse."""
    return str(response.json()["error"]["code"])
