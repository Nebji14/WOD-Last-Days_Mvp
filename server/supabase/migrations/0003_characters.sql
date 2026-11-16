-- 0003_characters.sql
-- Personnages joueurs et leurs feuilles (MLD : feuille_personnage, feuille_pj et
-- tables rattachées ; US-007 à US-010, US-026, US-027).
--
-- Adaptation du MLD :
--   * `character` porte ce qui est commun à toutes les formes d'un personnage :
--     propriétaire, expérience, notes, avantage surnaturel et éveil (maquette 05,
--     Q05-8 et Q05-15) ;
--   * `character_sheet` est une forme du personnage (onglets de la fiche,
--     ÉCART 2). La forme principale existe toujours et n'est pas supprimable ;
--   * atouts, handicaps, pouvoirs, objets, armes et armures partagent la table
--     `sheet_entry`, distingués par `kind` ; des contraintes réservent à chaque
--     type ses colonnes ;
--   * les notes sont rattachées au personnage, pas au compte (ÉCART 1) ;
--   * le solde d'expérience n'est pas stocké : total acquis moins dépenses (RM-017) ;
--   * les feuilles de PNJ feront l'objet d'une migration propre (US-039 à US-043).
--
-- Sécurité : RLS activée sans aucune politique sur toutes les tables. Seul le
-- serveur FastAPI les lit et les écrit.

create table public.character (
    id                 uuid primary key default gen_random_uuid(),
    owner_id           uuid not null references public.account (id) on delete restrict,
    awakened_at        timestamptz,
    supernatural_level smallint not null default 1,
    supernatural_name  text not null default '',
    xp_general_total   integer not null default 0,
    xp_tactical_total  integer not null default 0,
    created_at         timestamptz not null default now(),

    constraint character_id_owner_key unique (id, owner_id),
    constraint character_supernatural_level_range check (supernatural_level between 1 and 10),
    constraint character_supernatural_name_length check (char_length(supernatural_name) <= 60),
    constraint character_xp_general_range check (xp_general_total between 0 and 99999),
    constraint character_xp_tactical_range check (xp_tactical_total between 0 and 99999)
);

comment on table public.character is
    'Personnage joueur : données communes à toutes ses formes (MLD : feuille_pj).';
comment on column public.character.awakened_at is
    'Date de l''éveil déclenché par le MJ ; NULL tant qu''il ne l''est pas. Secret : jamais transmis au joueur avant le déclenchement.';
comment on column public.character.supernatural_level is
    'Avantage surnaturel, de 1 à 10 (maquette 05, ÉCART 3).';

create index character_owner_idx on public.character (owner_id);

-- Personnage joué à la table (Q03-5) : il appartient forcément au compte.
alter table public.account
    add column played_character_id uuid,
    add constraint account_played_character_fkey
        foreign key (played_character_id, id)
        references public.character (id, owner_id)
        on delete set null (played_character_id);

comment on column public.account.played_character_id is
    'Personnage affiché sur le siège du joueur ; NULL s''il n''en a pas.';

create table public.character_sheet (
    id                uuid primary key default gen_random_uuid(),
    character_id      uuid not null references public.character (id) on delete cascade,
    is_main           boolean not null default false,
    form_name         text not null,

    name              text not null,
    concept           text not null default '',
    profession        text not null default '',
    virtue            text not null default '',
    vice              text not null default '',
    compact           text not null default '',

    age               text not null default '',
    height            text not null default '',
    weight            text not null default '',
    sex               text not null default '',
    hair              text not null default '',
    eyes              text not null default '',
    origin            text not null default '',
    nationality       text not null default '',
    history           text not null default '',
    description       text not null default '',

    intelligence      smallint not null default 1 check (intelligence between 1 and 10),
    wits              smallint not null default 1 check (wits between 1 and 10),
    resolve           smallint not null default 1 check (resolve between 1 and 10),
    strength          smallint not null default 1 check (strength between 1 and 10),
    dexterity         smallint not null default 1 check (dexterity between 1 and 10),
    stamina           smallint not null default 1 check (stamina between 1 and 10),
    presence          smallint not null default 1 check (presence between 1 and 10),
    manipulation      smallint not null default 1 check (manipulation between 1 and 10),
    composure         smallint not null default 1 check (composure between 1 and 10),

    academics         smallint not null default 0 check (academics between 0 and 5),
    computer          smallint not null default 0 check (computer between 0 and 5),
    crafts            smallint not null default 0 check (crafts between 0 and 5),
    investigation     smallint not null default 0 check (investigation between 0 and 5),
    medicine          smallint not null default 0 check (medicine between 0 and 5),
    occult            smallint not null default 0 check (occult between 0 and 5),
    politics          smallint not null default 0 check (politics between 0 and 5),
    science           smallint not null default 0 check (science between 0 and 5),
    athletics         smallint not null default 0 check (athletics between 0 and 5),
    brawl             smallint not null default 0 check (brawl between 0 and 5),
    drive             smallint not null default 0 check (drive between 0 and 5),
    firearms          smallint not null default 0 check (firearms between 0 and 5),
    larceny           smallint not null default 0 check (larceny between 0 and 5),
    stealth           smallint not null default 0 check (stealth between 0 and 5),
    survival          smallint not null default 0 check (survival between 0 and 5),
    weaponry          smallint not null default 0 check (weaponry between 0 and 5),
    animal_ken        smallint not null default 0 check (animal_ken between 0 and 5),
    empathy           smallint not null default 0 check (empathy between 0 and 5),
    expression        smallint not null default 0 check (expression between 0 and 5),
    intimidation      smallint not null default 0 check (intimidation between 0 and 5),
    persuasion        smallint not null default 0 check (persuasion between 0 and 5),
    socialize         smallint not null default 0 check (socialize between 0 and 5),
    streetwise        smallint not null default 0 check (streetwise between 0 and 5),
    subterfuge        smallint not null default 0 check (subterfuge between 0 and 5),

    size              smallint not null check (size between 0 and 99),
    speed             smallint not null check (speed between 0 and 99),
    defense           smallint not null check (defense between 0 and 99),
    initiative        smallint not null check (initiative between 0 and 99),
    health_max        smallint not null check (health_max between 1 and 30),
    willpower_max     smallint not null check (willpower_max between 0 and 30),
    global_protection text not null default '',
    wound_track       text not null default '',
    willpower_current smallint not null,
    morality          smallint not null default 7 check (morality between 1 and 10),

    created_at        timestamptz not null default now(),

    constraint character_sheet_form_name_length check (char_length(form_name) between 1 and 60),
    constraint character_sheet_name_length check (char_length(name) between 1 and 80),
    constraint character_sheet_identity_length check (
        char_length(concept) <= 120 and char_length(profession) <= 120
        and char_length(virtue) <= 120 and char_length(vice) <= 120
        and char_length(compact) <= 120
    ),
    constraint character_sheet_description_length check (
        char_length(age) <= 60 and char_length(height) <= 60 and char_length(weight) <= 60
        and char_length(sex) <= 60 and char_length(hair) <= 60 and char_length(eyes) <= 60
        and char_length(origin) <= 120 and char_length(nationality) <= 120
        and char_length(history) <= 20000 and char_length(description) <= 20000
    ),
    constraint character_sheet_protection_length check (char_length(global_protection) <= 60),
    -- RM-008 : blessures rangées par gravité (* puis X puis /), sans autre caractère.
    constraint character_sheet_wound_order check (wound_track ~ '^\**X*/*$'),
    -- RM-011 : pas plus de blessures que de cases de santé.
    constraint character_sheet_wound_capacity check (char_length(wound_track) <= health_max),
    -- RM-011 : volonté disponible entre zéro et la volonté maximale.
    constraint character_sheet_willpower_range
        check (willpower_current between 0 and willpower_max)
);

comment on table public.character_sheet is
    'Forme d''un personnage : une feuille complète (MLD : feuille_personnage).';
comment on column public.character_sheet.is_main is
    'Forme principale : unique par personnage, jamais supprimable.';
comment on column public.character_sheet.size is
    'Valeur effective saisie (RM-005). La valeur de base est calculée, jamais stockée. Idem pour speed, defense, initiative, health_max et willpower_max.';
comment on column public.character_sheet.wound_track is
    'Piste de blessures : * aggravée, X létale, / contondante (RM-009).';

create index character_sheet_character_idx on public.character_sheet (character_id);
create unique index character_sheet_single_main_key
    on public.character_sheet (character_id)
    where is_main;

create table public.sheet_specialty (
    id       uuid primary key default gen_random_uuid(),
    sheet_id uuid not null references public.character_sheet (id) on delete cascade,
    skill    text not null,
    label    text not null,
    position smallint not null default 0,

    constraint sheet_specialty_skill_known check (skill in (
        'academics', 'computer', 'crafts', 'investigation', 'medicine', 'occult',
        'politics', 'science', 'athletics', 'brawl', 'drive', 'firearms', 'larceny',
        'stealth', 'survival', 'weaponry', 'animal_ken', 'empathy', 'expression',
        'intimidation', 'persuasion', 'socialize', 'streetwise', 'subterfuge'
    )),
    constraint sheet_specialty_label_length check (char_length(label) between 1 and 100)
);

comment on table public.sheet_specialty is
    'Spécialité d''une compétence : une ligne par spécialité (MLD : specialite_feuille).';

create index sheet_specialty_sheet_idx on public.sheet_specialty (sheet_id);

create table public.morality_note (
    id         uuid primary key default gen_random_uuid(),
    sheet_id   uuid not null references public.character_sheet (id) on delete cascade,
    level      smallint not null,
    body       text not null,
    created_at timestamptz not null default now(),

    constraint morality_note_level_range check (level between 1 and 10),
    constraint morality_note_body_length check (char_length(body) between 1 and 500)
);

comment on table public.morality_note is
    'Annotation de moralité, liée au niveau où elle a été acquise (RM-013 ; MLD : annotation_moralite).';

create index morality_note_sheet_idx on public.morality_note (sheet_id);

create table public.sheet_entry (
    id                   uuid primary key default gen_random_uuid(),
    sheet_id             uuid not null references public.character_sheet (id) on delete cascade,
    kind                 text not null,
    name                 text not null default '',
    description          text not null default '',
    level                smallint,
    quantity             integer,
    damage_modifier      smallint,
    range                text,
    size                 smallint,
    initiative_penalty   smallint,
    general_protection   smallint,
    ballistic_protection smallint,
    min_strength         smallint,
    defense_penalty      smallint,
    created_at           timestamptz not null default now(),

    constraint sheet_entry_kind_known
        check (kind in ('merit', 'flaw', 'power', 'item', 'weapon', 'armor')),
    constraint sheet_entry_text_length
        check (char_length(name) <= 120 and char_length(description) <= 4000
               and (range is null or char_length(range) <= 60)),
    constraint sheet_entry_number_range check (
        (level is null or level between 0 and 10)
        and (quantity is null or quantity between 0 and 9999)
        and (damage_modifier is null or damage_modifier between -20 and 20)
        and (size is null or size between 0 and 20)
        and (initiative_penalty is null or initiative_penalty between -20 and 20)
        and (general_protection is null or general_protection between 0 and 20)
        and (ballistic_protection is null or ballistic_protection between 0 and 20)
        and (min_strength is null or min_strength between 0 and 10)
        and (defense_penalty is null or defense_penalty between -20 and 20)
    ),
    -- Un atout a toujours un niveau ; il est facultatif pour un handicap ou un pouvoir.
    constraint sheet_entry_merit_level check (kind <> 'merit' or level is not null),
    constraint sheet_entry_level_scope
        check (kind in ('merit', 'flaw', 'power') or level is null),
    constraint sheet_entry_quantity_scope check (kind = 'item' or quantity is null),
    constraint sheet_entry_weapon_scope check (
        kind = 'weapon'
        or (damage_modifier is null and range is null and size is null
            and initiative_penalty is null)
    ),
    constraint sheet_entry_armor_scope check (
        kind = 'armor'
        or (general_protection is null and ballistic_protection is null
            and min_strength is null and defense_penalty is null)
    )
);

comment on table public.sheet_entry is
    'Élément d''une feuille : atout, handicap, pouvoir, objet, arme (RM-014) ou armure (MLD : atout, handicap, pouvoir, item, arme, armure).';

create index sheet_entry_sheet_idx on public.sheet_entry (sheet_id, kind);

create table public.tactic (
    id          uuid primary key default gen_random_uuid(),
    name        text not null default '',
    description text not null default '',
    created_at  timestamptz not null default now(),

    constraint tactic_text_length
        check (char_length(name) <= 120 and char_length(description) <= 4000)
);

comment on table public.tactic is
    'Tactique, partagée entre plusieurs feuilles (MLD : tactique, contrainte C06).';

create table public.sheet_tactic (
    sheet_id  uuid not null references public.character_sheet (id) on delete cascade,
    tactic_id uuid not null references public.tactic (id) on delete cascade,

    primary key (sheet_id, tactic_id)
);

comment on table public.sheet_tactic is
    'Tactiques connues d''une feuille (MLD : feuille_pj_tactique).';

create index sheet_tactic_tactic_idx on public.sheet_tactic (tactic_id);

create table public.xp_expense (
    id            uuid primary key default gen_random_uuid(),
    character_id  uuid not null references public.character (id) on delete cascade,
    is_tactical   boolean not null,
    points        integer not null,
    justification text not null,
    created_at    timestamptz not null default now(),

    constraint xp_expense_points_range check (points between 1 and 99999),
    -- RM-016 : justification obligatoire.
    constraint xp_expense_justification_length
        check (char_length(btrim(justification)) between 1 and 500)
);

comment on table public.xp_expense is
    'Dépense d''expérience générale ou tactique (RM-015, RM-016 ; MLD : depense_experience).';

create index xp_expense_character_idx on public.xp_expense (character_id);

create table public.character_note (
    id           uuid primary key default gen_random_uuid(),
    character_id uuid not null references public.character (id) on delete cascade,
    title        text not null default '',
    body         text not null default '',
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),

    constraint character_note_text_length
        check (char_length(title) <= 120 and char_length(body) <= 50000)
);

comment on table public.character_note is
    'Note de la fiche (face NOTES, 05c). Le propriétaire la gère ; le MJ la lit seulement.';

create index character_note_character_idx on public.character_note (character_id);

alter table public.character enable row level security;
alter table public.character_sheet enable row level security;
alter table public.sheet_specialty enable row level security;
alter table public.morality_note enable row level security;
alter table public.sheet_entry enable row level security;
alter table public.tactic enable row level security;
alter table public.sheet_tactic enable row level security;
alter table public.xp_expense enable row level security;
alter table public.character_note enable row level security;

revoke all on table
    public.character, public.character_sheet, public.sheet_specialty, public.morality_note,
    public.sheet_entry, public.tactic, public.sheet_tactic, public.xp_expense,
    public.character_note
from anon, authenticated;
