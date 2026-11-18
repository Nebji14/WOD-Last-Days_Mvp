"""Routes des ressources libres d'un personnage (Mana, Douleur…).

Chaque écriture renvoie le personnage à jour ; les droits sont ceux de la fiche.
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.characters import SheetWrite
from app.api.deps import ContainerDep, CurrentAccount
from app.schemas.character_requests import FieldUpdateRequest
from app.schemas.characters import AnyCharacterResponse, character_response
from app.schemas.resources import ResourceRequest

router = APIRouter(prefix="/api", tags=["resources"], dependencies=[SheetWrite])


@router.post("/characters/{character_id}/resources", status_code=status.HTTP_201_CREATED)
async def add_resource(
    character_id: UUID, payload: ResourceRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Ajoute une ressource, disponible à son maximum."""
    character = await container.resource_service.add(
        account, character_id, payload.name, payload.max_value
    )
    return character_response(character, account)


@router.patch("/resources/{resource_id}")
async def update_resource(
    resource_id: UUID,
    payload: FieldUpdateRequest,
    container: ContainerDep,
    account: CurrentAccount,
) -> AnyCharacterResponse:
    """Modifie le nom, le maximum ou la valeur disponible, sans écraser une autre saisie."""
    character = await container.resource_service.update(
        account, resource_id, payload.field, payload.value, payload.expected
    )
    return character_response(character, account)


@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.resource_service.delete(account, resource_id)
    return character_response(character, account)
