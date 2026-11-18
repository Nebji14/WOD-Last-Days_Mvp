"""Modèles d'entrée et de sortie des ressources libres."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.resources import NAME_MAX_LENGTH, VALUE_MAX, Resource


class ResourceRequest(BaseModel):
    """Création d'une ressource : son nom et son maximum."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    max_value: int = Field(ge=0, le=VALUE_MAX)


class ResourceResponse(BaseModel):
    """Ressource telle qu'elle est affichée sur la fiche."""

    id: UUID
    name: str
    max_value: int
    current_value: int

    @classmethod
    def from_resource(cls, resource: Resource) -> "ResourceResponse":
        return cls(
            id=resource.id,
            name=resource.name,
            max_value=resource.max_value,
            current_value=resource.current_value,
        )
