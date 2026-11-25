-- 0011_account_closure.sql
-- Désactivation et suppression définitive d'un compte joueur.
--
--   * `notice` marque une annonce de départ publiée dans le chat ;
--   * un message survit à la suppression de son auteur, sans son nom ;
--   * la trace d'un message supprimé reste même si le compte qui l'a supprimé
--     n'existe plus : seule la date la prouve alors.

alter table public.chat_message
    add column notice text,
    add constraint chat_message_notice_allowed
        check (notice in ('account_disabled', 'account_deleted')),
    alter column author_id drop not null,
    drop constraint chat_message_author_id_fkey,
    add constraint chat_message_author_id_fkey
        foreign key (author_id) references public.account (id) on delete set null,
    drop constraint chat_message_deleted_by_fkey,
    add constraint chat_message_deleted_by_fkey
        foreign key (deleted_by) references public.account (id) on delete set null,
    drop constraint chat_message_deletion_trace,
    add constraint chat_message_deletion_trace
        check (deleted_by is null or deleted_at is not null);

comment on column public.chat_message.notice is
    'Annonce publiée par le serveur (départ d''un joueur) ; NULL pour un message ordinaire.';
comment on column public.chat_message.author_id is
    'Auteur du message ; NULL si son compte a été supprimé définitivement.';
