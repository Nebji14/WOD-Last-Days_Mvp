-- 0006_dice_rolls.sql
-- Résultat des jets de dés, publié dans le chat.
--
-- Un jet terminé devient un message du chat dont le texte résume le résultat ;
-- la colonne `roll` garde le détail (réserve, faces, réussites) pour l'afficher.

alter table public.chat_message
    add column roll jsonb;

comment on column public.chat_message.roll is
    'Détail d''un jet de dés (réserve, faces de chaque vague, réussites) ; NULL pour un message ordinaire.';
