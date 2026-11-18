-- 0007_entry_rolls.sql
-- Recette de jet d'un pouvoir, d'une arme ou d'un atout.
--
-- Le joueur choisit, avec l'accord du MJ, les traits qui composent la réserve,
-- le coût en Volonté et un bonus fixe. Le serveur valide la recette ; la base
-- vérifie seulement qu'il s'agit d'un objet JSON.

alter table public.sheet_entry
    add column roll jsonb,
    add constraint sheet_entry_roll_object
        check (roll is null or jsonb_typeof(roll) = 'object');

comment on column public.sheet_entry.roll is
    'Recette de jet : {"parts": [...], "willpower_cost": n, "bonus": n} ; NULL sans jet.';
