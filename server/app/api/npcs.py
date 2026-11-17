"""Routes de l'outil PNJ du MJ et des données propres au PNJ.

Réservées au MJ. La feuille d'un PNJ (identité, santé, listes…)
passe par les routes des fiches, qui appliquent les mêmes droits.
"""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.characters import SheetWrite
from app.api.deps import ContainerDep, CurrentGm
from app.schemas.characters import AnyCharacterResponse, character_response
from app.schemas.npcs import (
    CategoryRenameRequest,
    CategoryRequest,
    CreatedResponse,
    CreateNpcRequest,
    MoveCategoryRequest,
    NpcDirectoryResponse,
    NpcFieldRequest,
)

_NO_CONTENT = status.HTTP_204_NO_CONTENT

router = APIRouter(prefix="/api", tags=["npcs"])


@router.get("/npcs")
async def get_directory(container: ContainerDep, _gm: CurrentGm) -> NpcDirectoryResponse:
    """Catégories et liste de tous les PNJ."""
    return NpcDirectoryResponse.from_directory(await container.npc_service.directory())


@router.post("/npcs", status_code=status.HTTP_201_CREATED, dependencies=[SheetWrite])
async def create_npc(
    payload: CreateNpcRequest, container: ContainerDep, gm: CurrentGm
) -> AnyCharacterResponse:
    """Crée une feuille de PNJ vierge du modèle choisi."""
    character = await container.npc_service.create(payload.model, payload.category_id)
    return character_response(character, gm)


@router.patch("/npcs/{character_id}", dependencies=[SheetWrite])
async def set_npc_field(
    character_id: UUID, payload: NpcFieldRequest, container: ContainerDep, gm: CurrentGm
) -> AnyCharacterResponse:
    """Modifie la catégorie, les notes intégrées ou Puissance / Finesse / Résilience."""
    character = await container.npc_service.set_field(
        gm, character_id, payload.field, payload.value, payload.expected
    )
    return character_response(character, gm)


@router.delete("/npcs/{character_id}", status_code=_NO_CONTENT, dependencies=[SheetWrite])
async def delete_npc(character_id: UUID, container: ContainerDep, gm: CurrentGm) -> Response:
    """Supprime définitivement la feuille du PNJ."""
    await container.npc_service.delete(gm, character_id)
    return Response(status_code=_NO_CONTENT)


@router.post("/npc-categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryRequest, container: ContainerDep, _gm: CurrentGm
) -> CreatedResponse:
    """Crée une catégorie, à la racine ou sous une catégorie."""
    category_id = await container.npc_service.create_category(payload.name, payload.parent_id)
    return CreatedResponse(id=category_id)


@router.patch("/npc-categories/{category_id}", status_code=_NO_CONTENT)
async def rename_category(
    category_id: UUID, payload: CategoryRenameRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Renomme une catégorie."""
    await container.npc_service.rename_category(category_id, payload.name)
    return Response(status_code=_NO_CONTENT)


@router.put("/npc-categories/{category_id}/parent", status_code=_NO_CONTENT)
async def move_category(
    category_id: UUID, payload: MoveCategoryRequest, container: ContainerDep, _gm: CurrentGm
) -> Response:
    """Range une catégorie sous une autre ; refusé s'il créerait un cycle."""
    await container.npc_service.move_category(category_id, payload.parent_id)
    return Response(status_code=_NO_CONTENT)


@router.delete("/npc-categories/{category_id}", status_code=_NO_CONTENT)
async def delete_category(category_id: UUID, container: ContainerDep, _gm: CurrentGm) -> Response:
    """Supprime une catégorie ; ses PNJ et sous-catégories remontent au parent."""
    await container.npc_service.delete_category(category_id)
    return Response(status_code=_NO_CONTENT)
