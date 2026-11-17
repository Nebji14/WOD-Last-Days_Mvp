"""Routes des personnages et de leurs formes (US-007 à US-010, US-026, US-027).

Toute route exige une session. Les droits (propriétaire ou MJ) sont contrôlés
par les services ; un personnage inaccessible répond comme un personnage absent.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import ContainerDep, CurrentAccount, enforce_rate_limit
from app.schemas.character_requests import (
    CreateCharacterRequest,
    FieldUpdateRequest,
    FormRequest,
    WoundRequest,
)
from app.schemas.characters import (
    AnyCharacterResponse,
    CharacterListResponse,
    character_response,
)

_WRITE_WINDOW_SECONDS = 10.0
_WRITE_LIMIT_PER_ACCOUNT = 80


async def limit_sheet_writes(container: ContainerDep, account: CurrentAccount) -> None:
    """Limite le débit des écritures sur les fiches, par compte.

    La limite laisse passer une saisie soutenue champ par champ.
    """
    enforce_rate_limit(
        container.rate_limiter,
        f"sheet:account:{account.id}",
        _WRITE_LIMIT_PER_ACCOUNT,
        _WRITE_WINDOW_SECONDS,
    )


SheetWrite = Depends(limit_sheet_writes)

router = APIRouter(prefix="/api", tags=["characters"])


@router.get("/characters")
async def list_characters(
    container: ContainerDep,
    account: CurrentAccount,
    owner: Annotated[UUID | None, Query()] = None,
) -> CharacterListResponse:
    """Liste mes personnages ; le MJ peut demander ceux d'un joueur (US-026 · CA1)."""
    characters = await container.character_service.list_for(account, owner or account.id)
    return CharacterListResponse(
        characters=[character_response(character, account) for character in characters]
    )


@router.post("/characters", status_code=status.HTTP_201_CREATED, dependencies=[SheetWrite])
async def create_character(
    payload: CreateCharacterRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Crée un personnage depuis l'assistant de création (US-007)."""
    character = await container.character_service.create(account, payload.to_input())
    return character_response(character, account)


@router.get("/characters/{character_id}")
async def get_character(
    character_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Retourne la fiche complète d'un personnage (US-008, US-026)."""
    character = await container.character_service.get(account, character_id)
    return character_response(character, account)


@router.delete(
    "/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[SheetWrite],
)
async def delete_character(
    character_id: UUID, container: ContainerDep, account: CurrentAccount
) -> Response:
    """Supprime définitivement un personnage (US-010)."""
    await container.character_service.delete(account, character_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/characters/{character_id}/play", dependencies=[SheetWrite])
async def play_character(
    character_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Désigne le personnage joué à la table (09-I4)."""
    character = await container.character_service.play(account, character_id)
    return character_response(character, account)


@router.post("/characters/{character_id}/awaken", dependencies=[SheetWrite])
async def awaken_character(
    character_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Déclenche l'éveil du personnage (04a-I5). Réservé au MJ, sans indice pour un joueur."""
    character = await container.awakening_service.awaken(account, character_id)
    return character_response(character, account)


@router.patch("/characters/{character_id}", dependencies=[SheetWrite])
async def update_character_field(
    character_id: UUID,
    payload: FieldUpdateRequest,
    container: ContainerDep,
    account: CurrentAccount,
) -> AnyCharacterResponse:
    """Modifie l'avantage surnaturel ou un total d'expérience (05-I10, RM-017)."""
    character = await container.character_service.set_character_field(
        account, character_id, payload.field, payload.value, payload.expected
    )
    return character_response(character, account)


@router.post(
    "/characters/{character_id}/forms",
    status_code=status.HTTP_201_CREATED,
    dependencies=[SheetWrite],
)
async def add_form(
    character_id: UUID, payload: FormRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Ajoute une forme, copie de la forme principale (05-F2)."""
    character = await container.character_service.add_form(account, character_id, payload.form_name)
    return character_response(character, account)


@router.patch("/sheets/{sheet_id}", dependencies=[SheetWrite])
async def update_sheet_field(
    sheet_id: UUID, payload: FieldUpdateRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Modifie un champ d'une forme, enregistré seul et aussitôt (US-009 · CA1)."""
    character = await container.character_service.set_sheet_field(
        account, sheet_id, payload.field, payload.value, payload.expected
    )
    return character_response(character, account)


@router.delete("/sheets/{sheet_id}", dependencies=[SheetWrite])
async def delete_form(
    sheet_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Supprime une forme alternative (05-F3)."""
    character = await container.character_service.delete_form(account, sheet_id)
    return character_response(character, account)


@router.post("/sheets/{sheet_id}/wounds", dependencies=[SheetWrite])
async def change_wounds(
    sheet_id: UUID, payload: WoundRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Ajoute, soigne ou aggrave une blessure (05-I4, RM-008, RM-011)."""
    character = await container.character_service.change_wounds(
        account, sheet_id, payload.action, payload.wound, payload.expected
    )
    return character_response(character, account)
