"""Routes des éléments d'une fiche.

Spécialités, annotations de moralité, éléments de feuille, tactiques, dépenses
d'expérience et notes. Chaque écriture renvoie le personnage à jour.
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.characters import SheetWrite
from app.api.deps import ContainerDep, CurrentAccount
from app.schemas.character_requests import (
    CreateEntryRequest,
    EntryValuesInput,
    ExpenseRequest,
    ExpenseUpdateRequest,
    MoralityNoteRequest,
    NoteUpdateRequest,
    SpecialtiesRequest,
    TacticRequest,
    TacticUpdateRequest,
)
from app.schemas.characters import (
    AnyCharacterResponse,
    NoteCreatedResponse,
    TacticListResponse,
    TacticResponse,
    character_response,
)

router = APIRouter(prefix="/api", tags=["sheet-items"], dependencies=[SheetWrite])
_CREATED = status.HTTP_201_CREATED


@router.put("/sheets/{sheet_id}/specialties/{skill}")
async def set_specialties(
    sheet_id: UUID,
    skill: str,
    payload: SpecialtiesRequest,
    container: ContainerDep,
    account: CurrentAccount,
) -> AnyCharacterResponse:
    """Remplace les spécialités d'une compétence."""
    character = await container.sheet_item_service.set_specialties(
        account, sheet_id, skill, payload.text
    )
    return character_response(character, account)


@router.post("/sheets/{sheet_id}/morality-notes", status_code=_CREATED)
async def add_morality_note(
    sheet_id: UUID, payload: MoralityNoteRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Ajoute une annotation de moralité."""
    character = await container.sheet_item_service.add_morality_note(
        account, sheet_id, payload.level, payload.body
    )
    return character_response(character, account)


@router.patch("/morality-notes/{note_id}")
async def update_morality_note(
    note_id: UUID, payload: MoralityNoteRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.update_morality_note(
        account, note_id, payload.level, payload.body
    )
    return character_response(character, account)


@router.delete("/morality-notes/{note_id}")
async def delete_morality_note(
    note_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.delete_morality_note(account, note_id)
    return character_response(character, account)


@router.post("/sheets/{sheet_id}/entries", status_code=_CREATED)
async def add_entry(
    sheet_id: UUID, payload: CreateEntryRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Ajoute un atout, un handicap, un pouvoir, un objet, une arme ou une armure."""
    character = await container.sheet_item_service.add_entry(
        account, sheet_id, payload.kind, payload.to_values()
    )
    return character_response(character, account)


@router.patch("/entries/{entry_id}")
async def update_entry(
    entry_id: UUID, payload: EntryValuesInput, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.update_entry(
        account, entry_id, payload.to_values()
    )
    return character_response(character, account)


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.delete_entry(account, entry_id)
    return character_response(character, account)


@router.get("/tactics")
async def list_tactics(container: ContainerDep, _: CurrentAccount) -> TacticListResponse:
    """Liste les tactiques existantes, pour en rattacher une à une feuille."""
    tactics = await container.sheet_item_service.list_tactics()
    return TacticListResponse(
        tactics=[TacticResponse(id=t.id, name=t.name, description=t.description) for t in tactics]
    )


@router.post("/sheets/{sheet_id}/tactics", status_code=_CREATED)
async def add_tactic(
    sheet_id: UUID, payload: TacticRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Rattache une tactique existante ou en crée une nouvelle."""
    service = container.sheet_item_service
    if payload.tactic_id is not None:
        character = await service.link_tactic(account, sheet_id, payload.tactic_id)
    else:
        character = await service.add_tactic(account, sheet_id, payload.name, payload.description)
    return character_response(character, account)


@router.patch("/sheets/{sheet_id}/tactics/{tactic_id}")
async def update_tactic(
    sheet_id: UUID,
    tactic_id: UUID,
    payload: TacticUpdateRequest,
    container: ContainerDep,
    account: CurrentAccount,
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.update_tactic(
        account, sheet_id, tactic_id, payload.name, payload.description
    )
    return character_response(character, account)


@router.delete("/sheets/{sheet_id}/tactics/{tactic_id}")
async def remove_tactic(
    sheet_id: UUID, tactic_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.remove_tactic(account, sheet_id, tactic_id)
    return character_response(character, account)


@router.post("/characters/{character_id}/xp-expenses", status_code=_CREATED)
async def add_expense(
    character_id: UUID, payload: ExpenseRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    """Enregistre une dépense d'expérience."""
    character = await container.sheet_item_service.add_expense(
        account, character_id, payload.is_tactical, payload.points, payload.justification
    )
    return character_response(character, account)


@router.patch("/xp-expenses/{expense_id}")
async def update_expense(
    expense_id: UUID,
    payload: ExpenseUpdateRequest,
    container: ContainerDep,
    account: CurrentAccount,
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.update_expense(
        account, expense_id, payload.points, payload.justification
    )
    return character_response(character, account)


@router.delete("/xp-expenses/{expense_id}")
async def delete_expense(
    expense_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.delete_expense(account, expense_id)
    return character_response(character, account)


@router.post("/characters/{character_id}/notes", status_code=_CREATED)
async def add_note(
    character_id: UUID, container: ContainerDep, account: CurrentAccount
) -> NoteCreatedResponse:
    """Crée une note vide, réservée au propriétaire de la fiche."""
    character, note_id = await container.sheet_item_service.add_note(account, character_id)
    return NoteCreatedResponse(character=character_response(character, account), note_id=note_id)


@router.patch("/notes/{note_id}")
async def update_note(
    note_id: UUID, payload: NoteUpdateRequest, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.update_note(
        account, note_id, payload.title, payload.body
    )
    return character_response(character, account)


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: UUID, container: ContainerDep, account: CurrentAccount
) -> AnyCharacterResponse:
    character = await container.sheet_item_service.delete_note(account, note_id)
    return character_response(character, account)
