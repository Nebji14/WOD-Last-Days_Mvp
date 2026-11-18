"""Routes des jets de dés."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import ContainerDep, CurrentAccount, rate_limit
from app.domain.dice import PoolOptions
from app.schemas.dice import RollRequest, RollResponse
from app.services.dice_pools import RollInput

router = APIRouter(prefix="/api/dice", tags=["dice"])

_WINDOW_SECONDS = 60.0
_ROLLS_PER_MINUTE = 30

RollLimit = Depends(rate_limit("dice", _ROLLS_PER_MINUTE, _WINDOW_SECONDS))


@router.post("/rolls", status_code=status.HTTP_201_CREATED, dependencies=[RollLimit])
async def roll(
    payload: RollRequest, account: CurrentAccount, container: ContainerDep
) -> RollResponse:
    """Lance un jet devant la table."""
    options = PoolOptions(
        specialty=payload.specialty,
        willpower=payload.willpower,
        modifier=payload.modifier,
        gm_bonus=payload.gm_bonus,
        again=payload.again,
        rote=payload.rote,
    )
    request = RollInput(
        kind=payload.kind,
        options=options,
        character_id=payload.character_id,
        sheet_id=payload.sheet_id,
        attribute=payload.attribute,
        second=payload.second,
        trait=payload.trait,
        dice=payload.dice,
        entry_id=payload.entry_id,
        secret=payload.secret,
    )
    result = await container.dice_service.start(account, request)
    return RollResponse.from_roll(result)


@router.post("/rolls/{roll_id}/reroll", dependencies=[RollLimit])
async def reroll(roll_id: UUID, account: CurrentAccount, container: ContainerDep) -> RollResponse:
    """Relance les dés en attente (10, ou 9 et 8 avec les options)."""
    return RollResponse.from_roll(await container.dice_service.reroll(account, roll_id))
