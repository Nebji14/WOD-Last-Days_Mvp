/**
 * Modèle d'un personnage et de ses fiches, tel que le renvoie l'API.
 *
 * Les noms d'attributs et de compétences sont ceux du serveur ; leurs libellés
 * français sont dans les fichiers de libellés.
 */
import { ApiError, isRecord } from "@/shared/api/client";

export type Category = "mental" | "physical" | "social";
export const CATEGORIES: readonly Category[] = ["mental", "physical", "social"];

export const ATTRIBUTES = {
  mental: ["intelligence", "wits", "resolve"],
  physical: ["strength", "dexterity", "stamina"],
  social: ["presence", "manipulation", "composure"],
} as const;

export const SKILLS = {
  mental: [
    "academics",
    "computer",
    "crafts",
    "investigation",
    "medicine",
    "occult",
    "politics",
    "science",
  ],
  physical: [
    "athletics",
    "brawl",
    "drive",
    "firearms",
    "larceny",
    "stealth",
    "survival",
    "weaponry",
  ],
  social: [
    "animal_ken",
    "empathy",
    "expression",
    "intimidation",
    "persuasion",
    "socialize",
    "streetwise",
    "subterfuge",
  ],
} as const;

export type AttributeName = (typeof ATTRIBUTES)[Category][number];
export type SkillName = (typeof SKILLS)[Category][number];

/** Plafond ordinaire d'un attribut ; 10 pour un personnage éveillé. */
export const ATTRIBUTE_MAX = 5;
export const ATTRIBUTE_MAX_AWAKENED = 10;
export const SKILL_MAX = 5;

export type EntryKind = "merit" | "flaw" | "power" | "item" | "weapon" | "armor";

export const ENTRY_NUMBER_FIELDS = [
  "level",
  "quantity",
  "damage_modifier",
  "size",
  "initiative_penalty",
  "general_protection",
  "ballistic_protection",
  "min_strength",
  "defense_penalty",
] as const;
export type EntryNumberField = (typeof ENTRY_NUMBER_FIELDS)[number];

/**
 * Recette de jet d'un pouvoir, d'une arme ou d'un atout : traits de la
 * réserve (attributs, compétences, `supernatural`, `entry_level`,
 * `weapon_bonus`), coût en Volonté, coût dans une ressource libre et bonus
 * fixe. Les deux coûts se cumulent.
 */
export interface RollRecipe {
  readonly parts: readonly string[];
  readonly willpower_cost: number;
  readonly bonus: number;
  /** Ressource libre dépensée ; absente ou `null` sans coût en ressource. */
  readonly resource_id?: string | null;
  readonly resource_cost?: number;
}

/** Ressource libre du personnage (Mana, Douleur…), commune à toutes ses formes. */
export interface Resource {
  readonly id: string;
  readonly name: string;
  readonly max_value: number;
  readonly current_value: number;
}

export const RESOURCE_VALUE_MAX = 30;
export const RESOURCE_NAME_MAX = 40;

export type Entry = {
  readonly id: string;
  readonly kind: EntryKind;
  readonly name: string;
  readonly description: string;
  readonly range: string | null;
  /** Absente pour un élément sans jet. */
  readonly roll?: RollRecipe | null;
} & { readonly [field in EntryNumberField]: number | null };

export interface MoralityNote {
  readonly id: string;
  readonly level: number;
  readonly body: string;
}

export interface Tactic {
  readonly id: string;
  readonly name: string;
  readonly description: string;
}

export interface Expense {
  readonly id: string;
  readonly is_tactical: boolean;
  readonly points: number;
  readonly justification: string;
  readonly created_at: string;
}

export interface Note {
  readonly id: string;
  readonly title: string;
  readonly body: string;
  readonly updated_at: string;
}

export type EffectiveField =
  "size" | "speed" | "defense" | "initiative" | "health_max" | "willpower_max";

export interface Sheet {
  readonly id: string;
  readonly is_main: boolean;
  readonly form_name: string;
  readonly texts: Readonly<Record<string, string>>;
  readonly attributes: Readonly<Record<AttributeName, number>>;
  readonly skills: Readonly<Record<SkillName, number>>;
  /** Valeurs saisies et stockées. */
  readonly effective: Readonly<Record<EffectiveField, number>>;
  /** Valeurs de référence calculées par le serveur, jamais stockées. */
  readonly base: Readonly<Record<EffectiveField, number>>;
  readonly wound_track: string;
  readonly willpower_current: number;
  readonly morality: number;
  readonly specialties: Readonly<Partial<Record<SkillName, readonly string[]>>>;
  readonly morality_notes: readonly MoralityNote[];
  readonly entries: readonly Entry[];
  readonly tactics: readonly Tactic[];
  /** Nom du fichier de l'image de cette forme, `null` sans image. */
  readonly portrait: string | null;
}

export interface Experience {
  readonly total: number;
  readonly balance: number;
}

/** Modèle d'un PNJ, choisi à la création. */
export type NpcModel = "full" | "simplified";

/** Données propres à une feuille de PNJ, lues par le MJ seul. */
export interface NpcProfile {
  readonly model: NpcModel;
  readonly category_id: string | null;
  readonly notes: string;
  /** Puissance, Finesse, Résilience : de 1 à 10 en simplifié, `null` en complet. */
  readonly power: number | null;
  readonly finesse: number | null;
  readonly resilience: number | null;
}

export interface Character {
  readonly id: string;
  /** Propriétaire du personnage joueur ; `null` pour un PNJ. */
  readonly owner_id: string | null;
  readonly owner_name: string;
  readonly is_played: boolean;
  readonly can_manage_notes: boolean;
  readonly supernatural_level: number;
  readonly supernatural_name: string;
  readonly xp_general: Experience;
  readonly xp_tactical: Experience;
  readonly sheets: readonly Sheet[];
  readonly expenses: readonly Expense[];
  readonly notes: readonly Note[];
  /** Présent et vrai uniquement pour un personnage éveillé. */
  readonly awakened?: true;
  /** Présent uniquement pour le MJ : date de l'éveil, ou `null`. */
  readonly awakened_at?: string | null;
  /** Profil du PNJ ; `null` ou absent pour un personnage joueur. */
  readonly npc?: NpcProfile | null;
  readonly resources: readonly Resource[];
}

/** Profil du PNJ, ou `null` pour un personnage joueur. */
export function npcProfile(character: Character): NpcProfile | null {
  return character.npc ?? null;
}

/** PNJ simplifié : ni attributs, ni compétences, ni base calculée. */
export function isSimplifiedNpc(character: Character): boolean {
  return character.npc?.model === "simplified";
}

/** Plafond des attributs de ce personnage, d'après ce que le serveur en dit au lecteur. */
export function attributeMax(character: Character): number {
  // Un PNJ a des points libres : attributs jusqu'à 10, comme après l'éveil.
  return character.awakened === true ||
    typeof character.awakened_at === "string" ||
    character.npc != null
    ? ATTRIBUTE_MAX_AWAKENED
    : ATTRIBUTE_MAX;
}

export function mainSheet(character: Character): Sheet {
  const main = character.sheets.find((sheet) => sheet.is_main) ?? character.sheets[0];
  if (main === undefined) {
    throw new ApiError(502, "internal_error");
  }
  return main;
}

function isSheet(value: unknown): value is Sheet {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.is_main === "boolean" &&
    typeof value.form_name === "string" &&
    isRecord(value.texts) &&
    isRecord(value.attributes) &&
    isRecord(value.skills) &&
    isRecord(value.effective) &&
    isRecord(value.base) &&
    typeof value.wound_track === "string" &&
    typeof value.willpower_current === "number" &&
    typeof value.morality === "number" &&
    isRecord(value.specialties) &&
    Array.isArray(value.morality_notes) &&
    Array.isArray(value.entries) &&
    Array.isArray(value.tactics)
  );
}

function isExperience(value: unknown): value is Experience {
  return isRecord(value) && typeof value.total === "number" && typeof value.balance === "number";
}

/**
 * Valide la structure d'un personnage renvoyé par l'API.
 *
 * @throws {ApiError} si la réponse n'a pas la forme attendue.
 */
export function parseCharacter(data: unknown): Character {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    (typeof data.owner_id === "string" || data.owner_id === null) &&
    typeof data.owner_name === "string" &&
    typeof data.is_played === "boolean" &&
    typeof data.can_manage_notes === "boolean" &&
    typeof data.supernatural_level === "number" &&
    typeof data.supernatural_name === "string" &&
    isExperience(data.xp_general) &&
    isExperience(data.xp_tactical) &&
    Array.isArray(data.sheets) &&
    data.sheets.length > 0 &&
    data.sheets.every(isSheet) &&
    Array.isArray(data.expenses) &&
    Array.isArray(data.notes)
  ) {
    // Un serveur pas encore à jour n'envoie ni les ressources ni les portraits : la
    // fiche s'affiche sans.
    const resources = Array.isArray(data.resources) ? data.resources : [];
    const sheets = data.sheets.map((sheet) => ({ ...sheet, portrait: sheet.portrait ?? null }));
    return { ...data, resources, sheets } as unknown as Character;
  }
  throw new ApiError(502, "internal_error");
}
