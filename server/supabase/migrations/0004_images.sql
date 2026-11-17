-- 0004_images.sql
-- Bibliothèque d'images du MJ, dossiers et scène de la table (US-031, écrans 04b et 08a).
--
-- Adaptation du MLD :
--   * `image` : `reference_fichier` devient `storage_path`, chemin de l'objet
--     dans le bucket privé `images` de Supabase Storage. Le nom du fichier est
--     régénéré par le serveur (identifiant aléatoire + extension du type réel) ;
--   * `image_folder` : nouvelle entité Dossier d'images (décision du chef de
--     projet du 2026-11-16), sur le modèle de la catégorie de PNJ (C07). Une
--     image est rangée dans 0 ou 1 dossier (Q04b-3). Les cycles de plusieurs
--     dossiers sont refusés par le serveur ; la base refuse le cas direct ;
--   * scène de la table (vision maquette, Q03MJ-1) : `is_shown` marque l'image
--     affichée en grand (une seule à la fois), `on_table_at` la date où elle a
--     été posée sur la pile (NULL = hors de la table).
--
-- Sécurité : RLS activée sans aucune politique. Seul le serveur FastAPI lit et
-- écrit ces tables. Le bucket est privé ; les fichiers ne sont lus que par des
-- URL signées à durée limitée, produites par le serveur.

create table public.image_folder (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    parent_id  uuid references public.image_folder (id) on delete restrict,
    created_at timestamptz not null default now(),

    constraint image_folder_name_length check (char_length(name) between 1 and 60),
    constraint image_folder_not_own_parent check (parent_id is null or parent_id <> id)
);

comment on table public.image_folder is
    'Dossier de la bibliothèque d''images (04b). Parent facultatif, sans cycle.';

create index image_folder_parent_idx on public.image_folder (parent_id);

create table public.image (
    id           uuid primary key default gen_random_uuid(),
    name         text not null,
    folder_id    uuid references public.image_folder (id) on delete restrict,
    storage_path text not null,
    content_type text not null,
    size_bytes   integer not null,
    is_shown     boolean not null default false,
    on_table_at  timestamptz,
    created_at   timestamptz not null default now(),

    constraint image_storage_path_key unique (storage_path),
    constraint image_name_length check (char_length(name) between 1 and 120),
    constraint image_storage_path_format
        check (storage_path ~ '^[0-9a-f]{32}\.(png|jpg|webp|gif)$'),
    constraint image_content_type_allowed
        check (content_type in ('image/png', 'image/jpeg', 'image/webp', 'image/gif')),
    constraint image_size_range check (size_bytes between 1 and 8388608)
);

comment on table public.image is
    'Image de la bibliothèque du MJ (MLD : image ; US-031 · CA1).';
comment on column public.image.storage_path is
    'Nom de l''objet dans le bucket privé « images », régénéré par le serveur.';
comment on column public.image.is_shown is
    'Image affichée en grand à la table, partie en pause (03-A2, 08a).';
comment on column public.image.on_table_at is
    'Date de pose sur la pile de la table ; NULL si l''image n''y est pas (US-031 · CA6).';

create index image_folder_id_idx on public.image (folder_id);
create unique index image_single_shown_idx on public.image (is_shown) where is_shown;

alter table public.image_folder enable row level security;
alter table public.image enable row level security;

revoke all on table public.image_folder from anon, authenticated;
revoke all on table public.image from anon, authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'images',
    'images',
    false,
    8388608,
    array['image/png', 'image/jpeg', 'image/webp', 'image/gif']
)
on conflict (id) do nothing;
