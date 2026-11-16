-- 0002_chat_messages.sql
-- Messages du chat général (MLD : message + message_compte ; US-013, US-029, US-030).
--
-- Adaptation du MLD :
--   * une seule table : les messages système et les messages privés (US-015)
--     sont hors MVP, la spécialisation C04 n'a donc qu'une branche ;
--   * `position` fixe l'ordre d'affichage et sert de curseur de pagination ;
--   * `client_token` rend l'envoi idempotent : un envoi rejoué après une
--     coupure (CDC 12.3) ne crée pas de doublon ;
--   * `est_supprime` est remplacé par `deleted_at` et `deleted_by`, qui portent
--     la trace de suppression (US-030 · CA5). Le contenu est effacé.
--
-- Sécurité : RLS activée sans aucune politique. Seul le serveur FastAPI lit et
-- écrit cette table.

create table public.chat_message (
    id           uuid primary key default gen_random_uuid(),
    position     bigint generated always as identity,
    author_id    uuid not null references public.account (id) on delete restrict,
    client_token uuid not null,
    body         text,
    sent_at      timestamptz not null default now(),
    edited_at    timestamptz,
    deleted_at   timestamptz,
    deleted_by   uuid references public.account (id) on delete restrict,

    constraint chat_message_position_key unique (position),
    constraint chat_message_author_token_key unique (author_id, client_token),
    constraint chat_message_body_length
        check (body is null or char_length(body) between 1 and 2000),
    constraint chat_message_body_or_deleted
        check ((body is null) = (deleted_at is not null)),
    constraint chat_message_deletion_trace
        check ((deleted_at is null) = (deleted_by is null))
);

comment on table public.chat_message is
    'Message public du chat général (MLD : message + message_compte).';
comment on column public.chat_message.position is
    'Ordre d''envoi ; curseur de pagination de l''historique.';
comment on column public.chat_message.client_token is
    'Jeton choisi par le client pour un envoi ; unique par auteur (envoi idempotent).';
comment on column public.chat_message.body is
    'Texte du message ; NULL une fois le message supprimé.';
comment on column public.chat_message.deleted_by is
    'Compte qui a supprimé le message : son auteur ou le MJ (US-030).';

create index chat_message_deleted_by_idx
    on public.chat_message (deleted_by)
    where deleted_by is not null;

alter table public.chat_message enable row level security;

revoke all on table public.chat_message from anon, authenticated;
