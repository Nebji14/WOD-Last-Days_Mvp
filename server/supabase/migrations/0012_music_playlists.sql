-- 0012_music_playlists.sql
-- Playlists de musique préparées par le MJ.
--
-- Seules les playlists sont conservées : la lecture en cours et la file
-- d'attente vivent en mémoire du serveur. Un morceau est décrit par
-- l'identifiant de sa vidéo, son titre, sa chaîne et sa durée ; aucun fichier
-- audio n'est stocké.
--
-- Sécurité : RLS activée sans aucune politique. Seul le serveur FastAPI lit et
-- écrit ces tables.

create table public.music_playlist (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    created_at timestamptz not null default now(),

    constraint music_playlist_name_length
        check (char_length(btrim(name)) between 1 and 60 and char_length(name) <= 60)
);

comment on table public.music_playlist is 'Playlist de musique du MJ.';

create table public.music_playlist_track (
    id               uuid primary key default gen_random_uuid(),
    playlist_id      uuid not null references public.music_playlist (id) on delete cascade,
    position         bigint generated always as identity,
    video_id         text not null,
    title            text not null,
    channel          text not null,
    duration_seconds integer not null,

    constraint music_playlist_track_video_id check (video_id ~ '^[A-Za-z0-9_-]{11}$'),
    constraint music_playlist_track_title_length check (char_length(title) <= 200),
    constraint music_playlist_track_channel_length check (char_length(channel) <= 120),
    constraint music_playlist_track_duration check (duration_seconds > 0)
);

comment on table public.music_playlist_track is
    'Morceau d''une playlist ; position suit l''ordre d''ajout.';

create index music_playlist_track_playlist_idx
    on public.music_playlist_track (playlist_id, position);

alter table public.music_playlist enable row level security;
alter table public.music_playlist_track enable row level security;

revoke all on table public.music_playlist from anon, authenticated;
revoke all on table public.music_playlist_track from anon, authenticated;
