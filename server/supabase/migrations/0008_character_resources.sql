-- 0008_character_resources.sql
-- Ressources ajoutées à un personnage (Mana, Douleur…), en plus de la Volonté.
--
-- Une ressource est commune à toutes les formes du personnage. Comme la
-- Volonté, elle a un maximum saisi à la main et une valeur disponible qui
-- baisse quand on la dépense. Un pouvoir peut la dépenser dans sa recette de
-- jet (`sheet_entry.roll`, clés `resource_id` et `resource_cost`).

create table public.character_resource (
    id            uuid primary key default gen_random_uuid(),
    character_id  uuid not null references public.character (id) on delete cascade,
    name          text not null,
    max_value     smallint not null default 0,
    current_value smallint not null default 0,
    created_at    timestamptz not null default now(),

    constraint character_resource_name_length
        check (char_length(btrim(name)) between 1 and 40 and char_length(name) <= 40),
    constraint character_resource_max_range check (max_value between 0 and 30),
    constraint character_resource_current_range check (current_value between 0 and max_value)
);

comment on table public.character_resource is
    'Ressource libre d''un personnage (Mana, Douleur…) : maximum saisi, valeur disponible dépensée.';

create index character_resource_character_idx on public.character_resource (character_id);

-- Deux ressources d'un même personnage ne portent pas le même nom.
create unique index character_resource_name_idx
    on public.character_resource (character_id, lower(name));

alter table public.character_resource enable row level security;

revoke all on table public.character_resource from anon, authenticated;
