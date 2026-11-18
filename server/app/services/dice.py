"""Jets de dés lancés devant toute la table.

Le serveur tire les dés, pour que personne ne puisse truquer un jet, puis
diffuse chaque vague : le lancer, puis une seule vague de relance des 10 (ou
9, 8). Le lanceur déclenche la relance quand ses dés passent à l'écran ; s'il
est parti, le serveur relance seul après un long délai. Un jet terminé est
publié dans le chat, sauf le jet secret du MJ, montré au MJ seul.
"""

import asyncio
import logging
import secrets
from dataclasses import replace
from typing import Any, Protocol
from uuid import UUID, uuid4

from app.core.errors import AppError, ErrorCode
from app.domain.accounts import Account, Role
from app.domain.character import Character, Sheet
from app.domain.dice import (
    DIE_FACES,
    DiceRoll,
    DiceRuleError,
    DieRoller,
    PoolOptions,
    PoolPart,
    RollKind,
    bonus_parts,
    check_options,
    pool_size,
    rerolls_after,
    roll_detail,
    roll_dice,
)
from app.domain.recipes import RollRecipe
from app.services.character_access import CharacterAccess, rule_violation
from app.services.dice_pools import RollInput, compose_pool, entry_of

logger = logging.getLogger(__name__)


class WillpowerStore(Protocol):
    """Écriture de la volonté disponible, dépensée pour +3 dés."""

    async def update_sheet_field(
        self, sheet_id: UUID, field: str, value: str | int, expected: str | int
    ) -> bool: ...


class RollBroadcaster(Protocol):
    """Diffusion d'une vague de dés."""

    async def dice_rolled(self, data: dict[str, Any], recipients: set[UUID] | None) -> None: ...


class RollPublisher(Protocol):
    """Publication du résultat dans le chat."""

    async def publish_roll(
        self, author_id: UUID, roll_id: UUID, body: str, roll: dict[str, Any]
    ) -> Any: ...


def _random_die() -> int:
    return secrets.randbelow(DIE_FACES) + 1


def _roll_not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Ce jet est terminé.", status_code=404)


def _forbidden(message: str) -> AppError:
    return AppError(ErrorCode.FORBIDDEN, message, status_code=403)


class DiceService:
    """Orchestre les jets de dés.

    Args:
        access: droits et lecture des personnages.
        willpower: écriture de la volonté dépensée.
        broadcaster: diffusion des vagues de dés.
        publisher: publication du résultat dans le chat.
        roll_die: tirage d'un dé (remplacé dans les tests).
        auto_reroll_seconds: délai avant la relance automatique ; ``None`` la
            désactive.
    """

    def __init__(
        self,
        access: CharacterAccess,
        willpower: WillpowerStore,
        broadcaster: RollBroadcaster,
        publisher: RollPublisher,
        roll_die: DieRoller = _random_die,
        auto_reroll_seconds: float | None = None,
    ) -> None:
        self._access = access
        self._willpower = willpower
        self._broadcaster = broadcaster
        self._publisher = publisher
        self._roll_die = roll_die
        self._auto_delay = auto_reroll_seconds
        self._rolls: dict[UUID, DiceRoll] = {}
        self._lock = asyncio.Lock()
        self._timers: set[asyncio.Task[None]] = set()

    async def start(self, actor: Account, request: RollInput) -> DiceRoll:
        """Compose la réserve, lance la première vague et la diffuse.

        Raises:
            AppError: ``rule_violation`` pour une demande incohérente,
                ``forbidden`` pour un jet réservé au MJ, ``not_found`` pour un
                personnage inaccessible, ``edit_conflict`` si la volonté a changé.
        """
        options = request.options
        try:
            check_options(options)
        except DiceRuleError as error:
            raise rule_violation(str(error), "dice") from None
        if request.secret and actor.role is not Role.GM:
            raise _forbidden("Seul le MJ lance des dés en secret.")
        if request.kind is RollKind.FREE:
            roll = self._free_roll(actor, request)
        else:
            roll = await self._character_roll(actor, request)
        async with self._lock:
            self._rolls[roll.id] = roll
        await self._announce(roll)
        return roll

    async def reroll(self, actor: Account, roll_id: UUID) -> DiceRoll:
        """Relance les dés en attente, à la demande du lanceur.

        Raises:
            AppError: ``not_found`` si le jet est terminé ou inconnu,
                ``forbidden`` si ``actor`` n'est pas le lanceur.
        """
        roll = self._rolls.get(roll_id)
        if roll is None:
            raise _roll_not_found()
        if roll.roller_id != actor.id:
            raise _forbidden("Seul le lanceur relance ses dés.")
        advanced = await self._advance(roll_id, len(roll.stages))
        if advanced is None:
            raise _roll_not_found()
        return advanced

    def _free_roll(self, actor: Account, request: RollInput) -> DiceRoll:
        """Réserve libre du MJ : un nombre de dés, sans personnage."""
        if actor.role is not Role.GM or request.dice is None:
            raise _forbidden("La réserve libre est réservée au MJ.")
        modifier = PoolOptions(modifier=request.options.modifier)
        parts = [PoolPart("dice", request.dice), *bonus_parts(modifier, 0)]
        return self._first_stage(actor, actor.display_name, None, request, parts)

    async def _character_roll(self, actor: Account, request: RollInput) -> DiceRoll:
        """Jet tiré d'une feuille : réserve composée et volonté dépensée."""
        character = await self._access.editable(actor, request.character_id)
        if request.sheet_id is None:
            raise rule_violation("sheet", "dice")
        sheet = self._access.sheet_of(character, request.sheet_id)
        try:
            entry = entry_of(sheet, request)
            parts, base = compose_pool(character, sheet, request, entry)
        except DiceRuleError as error:
            raise rule_violation(str(error), "dice") from None
        # Le coût du pouvoir et la Volonté dépensée pour +3 se cumulent.
        recipe = None if entry is None else RollRecipe.from_data(entry.roll)
        cost = (1 if request.options.willpower else 0) + (recipe.willpower_cost if recipe else 0)
        if cost:
            await self._spend_willpower(character, sheet, cost)
        name = character.main_sheet.texts.get("name") or character.owner_name
        roll = self._first_stage(actor, name, character.id, request, parts)
        return replace(roll, base=base, label=None if entry is None else entry.name)

    async def _spend_willpower(self, character: Character, sheet: Sheet, amount: int) -> None:
        """Retire des points de volonté disponibles, sans écraser une modification concurrente."""
        current = sheet.numbers["willpower_current"]
        if current < amount:
            raise rule_violation("no_willpower", "willpower_current")
        if not await self._willpower.update_sheet_field(
            sheet.id, "willpower_current", current - amount, current
        ):
            raise AppError(ErrorCode.EDIT_CONFLICT, "La volonté a changé.", status_code=409)
        await self._access.changed(character.id)

    def _first_stage(
        self,
        actor: Account,
        name: str,
        character_id: UUID | None,
        request: RollInput,
        parts: list[PoolPart],
    ) -> DiceRoll:
        """Lance la première vague : la réserve, ou un dé de chance si elle est vide."""
        options = request.options
        initiative = request.kind is RollKind.INITIATIVE
        size = 1 if initiative else pool_size(parts)
        chance = not initiative and size == 0
        faces = roll_dice(max(size, 1), self._roll_die)
        pending = 0 if initiative else rerolls_after(faces, options.again, options.rote, chance)
        return DiceRoll(
            id=uuid4(),
            roller_id=actor.id,
            roller_role=actor.role,
            roller_name=name,
            character_id=character_id,
            kind=request.kind,
            parts=parts,
            chance=chance,
            again=options.again,
            rote=options.rote,
            secret=request.secret,
            stages=[faces],
            pending=pending,
        )

    async def _advance(self, roll_id: UUID, stage_count: int) -> DiceRoll | None:
        """Lance la vague suivante si le jet en est toujours à ``stage_count`` vagues."""
        async with self._lock:
            roll = self._rolls.get(roll_id)
            if roll is None or roll.finished or len(roll.stages) != stage_count:
                return None
            # Un dé ne se relance qu'une fois : la vague de relance clôt le jet.
            faces = roll_dice(roll.pending, self._roll_die)
            roll = replace(roll, stages=[*roll.stages, faces], pending=0)
            self._rolls[roll_id] = roll
        await self._announce(roll)
        return roll

    async def _announce(self, roll: DiceRoll) -> None:
        """Diffuse la vague ; publie le jet terminé ou programme la relance automatique."""
        detail = roll_detail(roll)
        recipients = None
        if roll.secret:
            recipients = {roll.roller_id} | await self._access.gm_recipients()
        await self._broadcaster.dice_rolled(detail, recipients)
        if not roll.finished:
            self._schedule_reroll(roll)
            return
        async with self._lock:
            self._rolls.pop(roll.id, None)
        if not roll.secret:
            await self._publisher.publish_roll(roll.roller_id, roll.id, roll_summary(roll), detail)

    def _schedule_reroll(self, roll: DiceRoll) -> None:
        """Relance seule après le délai si le lanceur n'a pas cliqué."""
        if self._auto_delay is None:
            return
        task = asyncio.create_task(self._auto_reroll(roll.id, len(roll.stages)))
        self._timers.add(task)
        task.add_done_callback(self._timers.discard)

    async def _auto_reroll(self, roll_id: UUID, stage_count: int) -> None:
        assert self._auto_delay is not None  # noqa: S101 - garanti par _schedule_reroll
        await asyncio.sleep(self._auto_delay)
        try:
            await self._advance(roll_id, stage_count)
        except Exception:
            logger.exception("Relance automatique impossible")


def roll_summary(roll: DiceRoll) -> str:
    """Texte du message de chat : il sert de repli au détail affiché par le client."""
    who = roll.roller_name if roll.label is None else f"{roll.roller_name} · {roll.label}"
    if roll.total is not None:
        return f"{who} · initiative {roll.total}"
    successes = roll.successes
    plural = "s" if successes > 1 else ""
    return f"{who} · {successes} réussite{plural}"
