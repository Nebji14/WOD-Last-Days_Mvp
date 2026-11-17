"""Modèles de sortie de l'outil Joueurs du MJ."""

from uuid import UUID

from pydantic import BaseModel

from app.domain.accounts import AccountStatus
from app.domain.players import PlayerSummary


class PlayerResponse(BaseModel):
    """Ligne de la liste des joueurs et données de compte affichées au MJ."""

    id: UUID
    username: str
    display_name: str
    status: AccountStatus
    online: bool
    character_names: list[str]

    @classmethod
    def from_summary(cls, summary: PlayerSummary) -> "PlayerResponse":
        """Projette une ligne du domaine, sans l'adresse technique du compte."""
        account = summary.record.account
        return cls(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            status=account.status,
            online=summary.online,
            character_names=list(summary.record.character_names),
        )


class PlayerListResponse(BaseModel):
    players: list[PlayerResponse]
