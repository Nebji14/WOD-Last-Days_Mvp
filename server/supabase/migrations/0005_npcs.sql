-- 0005_npcs.sql
-- Feuilles de PNJ et catégories (MLD : feuille_pnj, feuille_pnj_complete,
-- feuille_pnj_simplifiee, categorie_pnj ; US-039 à US-043, écrans 04c et 07).
--
-- Adaptation du MLD :
--   * un PNJ est un `character` de nature `npc`, sans propriétaire : il réutilise
--     la feuille (`character_sheet`) et ses listes (atouts, armes, moralité…),
--     comme la feuille de personnage mère du MLD. Un personnage joueur garde
--     obligatoirement son propriétaire ;
--   * `npc_profile` porte ce qui est propre au PNJ (MLD : feuille_pnj et ses
--     deux filles) : modèle complet ou simplifié (RM-021), catégorie, notes
--     intégrées, et Puissance, Finesse, Résilience de 1 à 10 pour le modèle
--     simplifié seulement (RM-022) ;
--   * un PNJ n'a ni expérience, ni tactiques, ni formes, ni notes autonomes :
--     le serveur refuse ces écritures ;
--   * `npc_category` : catégorie et sous-catégories (C07). Les cycles de
--     plusieurs catégories sont refusés par le serveur ; la base refuse le cas
--     direct. Un PNJ est dans 0 ou 1 catégorie (Q04c-3).
--
-- Sécurité : RLS activée sans aucune politique. Seul le serveur FastAPI lit et
-- écrit ces tables.

create table public.npc_category (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    parent_id  uuid references public.npc_category (id) on delete restrict,
    created_at timestamptz not null default now(),

    constraint npc_category_name_length check (char_length(name) between 1 and 60),
    constraint npc_category_not_own_parent check (parent_id is null or parent_id <> id)
);

comment on table public.npc_category is
    'Catégorie de PNJ (MLD : categorie_pnj, C07). Parent facultatif, sans cycle.';

create index npc_category_parent_idx on public.npc_category (parent_id);

alter table public.character
    add column kind text not null default 'pc',
    alter column owner_id drop not null,
    add constraint character_kind_allowed check (kind in ('pc', 'npc')),
    add constraint character_owner_by_kind check ((kind = 'pc') = (owner_id is not null));

comment on column public.character.kind is
    'pc : personnage joueur, avec propriétaire ; npc : PNJ du MJ, sans propriétaire.';

create table public.npc_profile (
    character_id uuid primary key references public.character (id) on delete cascade,
    model        text not null,
    category_id  uuid references public.npc_category (id) on delete restrict,
    notes        text not null default '',
    power        smallint,
    finesse      smallint,
    resilience   smallint,

    constraint npc_profile_model_allowed check (model in ('full', 'simplified')),
    constraint npc_profile_notes_length check (char_length(notes) <= 20000),
    -- RM-022 : Puissance, Finesse et Résilience, de 1 à 10, pour le modèle simplifié seul.
    constraint npc_profile_simplified_traits check (
        (model = 'simplified'
            and power between 1 and 10
            and finesse between 1 and 10
            and resilience between 1 and 10)
        or (model = 'full' and power is null and finesse is null and resilience is null)
    )
);

comment on table public.npc_profile is
    'Données propres à une feuille de PNJ (MLD : feuille_pnj et ses deux spécialisations).';
comment on column public.npc_profile.notes is
    'Notes intégrées du PNJ, distinctes des notes autonomes (US-039 · CA7).';

create index npc_profile_category_idx on public.npc_profile (category_id);

alter table public.npc_category enable row level security;
alter table public.npc_profile enable row level security;

revoke all on table public.npc_category from anon, authenticated;
revoke all on table public.npc_profile from anon, authenticated;
