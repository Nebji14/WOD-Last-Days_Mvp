-- 0010_account_portrait.sql
-- Photo du maître du jeu, rattachée à son compte : il n'a pas de personnage.
--
-- Le fichier est déposé dans le bucket privé `images`, sous un nom régénéré par
-- le serveur. La photo d'un joueur est celle de son personnage.

alter table public.account
    add column portrait_path text,
    add constraint account_portrait_path_key unique (portrait_path),
    add constraint account_portrait_path_format
        check (portrait_path ~ '^[0-9a-f]{32}\.(png|jpg|webp|gif)$');

comment on column public.account.portrait_path is
    'Nom du fichier de la photo du compte dans le bucket privé « images » ; NULL sans photo.';
