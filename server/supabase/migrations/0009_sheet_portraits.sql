-- 0009_sheet_portraits.sql
-- Image de chaque forme d'un personnage (portrait), joueur ou PNJ.
--
-- Le fichier est déposé dans le bucket privé `images`, sous un nom régénéré par
-- le serveur. Une nouvelle forme ne reprend pas l'image de la forme principale.

alter table public.character_sheet
    add column portrait_path text,
    add constraint character_sheet_portrait_path_key unique (portrait_path),
    add constraint character_sheet_portrait_path_format
        check (portrait_path ~ '^[0-9a-f]{32}\.(png|jpg|webp|gif)$');

comment on column public.character_sheet.portrait_path is
    'Nom du fichier de l''image de cette forme dans le bucket privé « images » ; NULL sans image.';
