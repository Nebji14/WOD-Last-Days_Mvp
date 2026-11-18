"""Lecture d'un personnage complet en une seule requête.

Le personnage, ses formes et tout ce qui s'y rattache sont assemblés par
PostgreSQL en un document JSON, puis convertis en objets du domaine. Une fiche
se lit ainsi en un aller-retour vers la base.
"""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.character import (
    Character,
    Entry,
    EntryKind,
    Expense,
    MoralityNote,
    Note,
    Sheet,
    Tactic,
)
from app.domain.npc_profile import NpcModel, NpcProfile
from app.domain.sheet_fields import NUMBER_FIELDS, TEXT_FIELDS
from app.domain.traits import ATTRIBUTE_NAMES, SKILL_NAMES

# Requête de lecture ; à compléter par une clause ``where`` sur ``c``.
SELECT_DOCUMENT = """
    select jsonb_build_object(
        'id', c.id,
        'owner_id', c.owner_id,
        'owner_name', coalesce(a.display_name, ''),
        'npc', (
            select jsonb_build_object(
                'model', p.model, 'category_id', p.category_id, 'notes', p.notes,
                'power', p.power, 'finesse', p.finesse, 'resilience', p.resilience)
            from npc_profile p where p.character_id = c.id),
        'awakened_at', c.awakened_at,
        'supernatural_level', c.supernatural_level,
        'supernatural_name', c.supernatural_name,
        'xp_general_total', c.xp_general_total,
        'xp_tactical_total', c.xp_tactical_total,
        'is_played', coalesce(a.played_character_id = c.id, false),
        'sheets', (
            select coalesce(jsonb_agg(to_jsonb(s) || jsonb_build_object(
                'specialties', (
                    select coalesce(jsonb_agg(
                        jsonb_build_object('skill', sp.skill, 'label', sp.label)
                        order by sp.position, sp.id), '[]'::jsonb)
                    from sheet_specialty sp where sp.sheet_id = s.id),
                'morality_notes', (
                    select coalesce(jsonb_agg(to_jsonb(mn)
                        order by mn.level desc, mn.created_at, mn.id), '[]'::jsonb)
                    from morality_note mn where mn.sheet_id = s.id),
                'entries', (
                    select coalesce(jsonb_agg(to_jsonb(e)
                        order by e.created_at, e.id), '[]'::jsonb)
                    from sheet_entry e where e.sheet_id = s.id),
                'tactics', (
                    select coalesce(jsonb_agg(to_jsonb(t)
                        order by t.created_at, t.id), '[]'::jsonb)
                    from sheet_tactic st join tactic t on t.id = st.tactic_id
                    where st.sheet_id = s.id)
            ) order by s.is_main desc, s.created_at, s.id), '[]'::jsonb)
            from character_sheet s where s.character_id = c.id),
        'expenses', (
            select coalesce(jsonb_agg(to_jsonb(x)
                order by x.created_at desc, x.id), '[]'::jsonb)
            from xp_expense x where x.character_id = c.id),
        'notes', (
            select coalesce(jsonb_agg(to_jsonb(n)
                order by n.updated_at desc, n.id), '[]'::jsonb)
            from character_note n where n.character_id = c.id)
    ) as document
    from character c
    left join account a on a.id = c.owner_id
"""


def to_character(raw: str) -> Character:
    """Convertit le document JSON produit par ``SELECT_DOCUMENT``."""
    document: dict[str, Any] = json.loads(raw)
    awakened_at = document["awakened_at"]
    return Character(
        id=UUID(document["id"]),
        owner_id=UUID(document["owner_id"]) if document["owner_id"] else None,
        owner_name=document["owner_name"],
        awakened_at=datetime.fromisoformat(awakened_at) if awakened_at else None,
        supernatural_level=document["supernatural_level"],
        supernatural_name=document["supernatural_name"],
        xp_general_total=document["xp_general_total"],
        xp_tactical_total=document["xp_tactical_total"],
        is_played=document["is_played"],
        sheets=[_to_sheet(sheet) for sheet in document["sheets"]],
        expenses=[
            Expense(
                id=UUID(expense["id"]),
                is_tactical=expense["is_tactical"],
                points=expense["points"],
                justification=expense["justification"],
                created_at=datetime.fromisoformat(expense["created_at"]),
            )
            for expense in document["expenses"]
        ],
        notes=[
            Note(
                id=UUID(note["id"]),
                title=note["title"],
                body=note["body"],
                updated_at=datetime.fromisoformat(note["updated_at"]),
            )
            for note in document["notes"]
        ],
        npc=to_npc_profile(document["npc"]) if document["npc"] else None,
    )


def to_npc_profile(raw: dict[str, Any]) -> NpcProfile:
    """Convertit le profil de PNJ lu en JSON (ou en ligne de base) en objet du domaine."""
    category_id = raw["category_id"]
    return NpcProfile(
        model=NpcModel(raw["model"]),
        category_id=UUID(str(category_id)) if category_id else None,
        notes=raw["notes"],
        power=raw["power"],
        finesse=raw["finesse"],
        resilience=raw["resilience"],
    )


def _to_sheet(row: dict[str, Any]) -> Sheet:
    specialties: dict[str, list[str]] = {}
    for specialty in row["specialties"]:
        specialties.setdefault(specialty["skill"], []).append(specialty["label"])
    return Sheet(
        id=UUID(row["id"]),
        is_main=row["is_main"],
        form_name=row["form_name"],
        texts={field: row[field] for field in TEXT_FIELDS if field != "form_name"},
        traits={name: row[name] for name in (*ATTRIBUTE_NAMES, *SKILL_NAMES)},
        numbers={field: row[field] for field in NUMBER_FIELDS},
        wound_track=row["wound_track"],
        specialties=specialties,
        morality_notes=[
            MoralityNote(id=UUID(note["id"]), level=note["level"], body=note["body"])
            for note in row["morality_notes"]
        ],
        entries=[_to_entry(entry) for entry in row["entries"]],
        tactics=[
            Tactic(id=UUID(t["id"]), name=t["name"], description=t["description"])
            for t in row["tactics"]
        ],
    )


def _to_entry(row: dict[str, Any]) -> Entry:
    return Entry(
        id=UUID(row["id"]),
        kind=EntryKind(row["kind"]),
        name=row["name"],
        description=row["description"],
        level=row["level"],
        quantity=row["quantity"],
        damage_modifier=row["damage_modifier"],
        range=row["range"],
        size=row["size"],
        initiative_penalty=row["initiative_penalty"],
        general_protection=row["general_protection"],
        ballistic_protection=row["ballistic_protection"],
        min_strength=row["min_strength"],
        defense_penalty=row["defense_penalty"],
        roll=row.get("roll"),
    )
