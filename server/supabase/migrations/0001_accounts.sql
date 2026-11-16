-- 0001_accounts.sql
-- Comptes de l'application (MLD : compte, compte_joueur, compte_mj).
--
-- Adaptation du MLD :
--   * les tables filles sans attribut propre (compte_joueur, compte_mj) sont
--     remplacées par la colonne discriminante `role` ;
--   * les méthodes de connexion (methode_connexion_*) sont déléguées à
--     Supabase Auth (auth.users, auth.identities), comme le MLD l'autorise ;
--   * `id` reprend l'identifiant de l'utilisateur Supabase Auth.
--
-- Sécurité : RLS activée sans aucune politique. Seul le serveur FastAPI
-- (connexion directe à la base) lit et écrit cette table.

create type public.account_role as enum ('player', 'gm');
create type public.account_status as enum ('active', 'disabled');

create table public.account (
    id           uuid primary key references auth.users (id) on delete restrict,
    username     text not null,
    display_name text not null,
    auth_email   text not null,
    role         public.account_role not null default 'player',
    status       public.account_status not null default 'active',
    created_at   timestamptz not null default now(),

    constraint account_username_format
        check (username ~ '^[A-Za-z0-9._-]{3,24}$'),
    constraint account_display_name_length
        check (char_length(display_name) between 1 and 40),
    constraint account_auth_email_length
        check (char_length(auth_email) between 3 and 254)
);

comment on table public.account is
    'Compte joueur ou MJ (MLD : compte + compte_joueur + compte_mj).';
comment on column public.account.username is
    'Nom d''utilisateur saisi à la connexion ; unique sans tenir compte de la casse.';
comment on column public.account.display_name is
    'Nom affiché dans le chat ; égal au nom d''utilisateur au MVP (Q02b-2).';
comment on column public.account.auth_email is
    'Adresse utilisée auprès de Supabase Auth : technique pour un joueur, réelle pour le MJ.';

-- Unicité insensible à la casse du nom d'utilisateur (02b-V1).
create unique index account_username_lower_key
    on public.account (lower(username));

create unique index account_auth_email_lower_key
    on public.account (lower(auth_email));

-- C01 : au plus un compte MJ.
create unique index account_single_gm_key
    on public.account ((true))
    where role = 'gm';

alter table public.account enable row level security;

revoke all on table public.account from anon, authenticated;
