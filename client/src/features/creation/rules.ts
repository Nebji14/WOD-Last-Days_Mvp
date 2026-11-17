/**
 * Règles de la création de personnage, reflétées côté client pour guider la
 * saisie (écran 06). Le serveur reste seul garant : il refait tous ces
 * contrôles à l'enregistrement.
 *
 * RM-001 attributs : 1 point gratuit, puis 5 / 4 / 3 selon la priorité.
 * RM-002 un attribut à 4 ou 5 déclenche une alerte non bloquante.
 * RM-003 compétences : 11 / 7 / 4, classement indépendant des attributs.
 * RM-004 trois spécialités sur des compétences à 1 point ou plus.
 * RM-006, RM-007, RM-010 valeurs de base de l'aperçu.
 */
import {
  ATTRIBUTE_MAX,
  ATTRIBUTES,
  type AttributeName,
  CATEGORIES,
  type Category,
  type EffectiveField,
  SKILL_MAX,
  type SkillName,
  SKILLS,
} from "@/features/characters/model";

export type Rank = 1 | 2 | 3;
export type TraitKind = "attributes" | "skills";
export type Priorities = Readonly<Record<Category, Rank>>;

export const ATTRIBUTE_BUDGETS: Readonly<Record<Rank, number>> = { 1: 5, 2: 4, 3: 3 };
export const SKILL_BUDGETS: Readonly<Record<Rank, number>> = { 1: 11, 2: 7, 3: 4 };
export const SPECIALTY_COUNT = 3;
const ATTRIBUTE_ALERT_THRESHOLD = 4;
const BASE_SIZE = 5;
const SPEED_BONUS = 5;

/** Point de départ et plafond d'un trait selon son type (RM-001, RM-003, Q05-2). */
export const TRAIT_BOUNDS: Readonly<Record<TraitKind, { min: number; max: number }>> = {
  attributes: { min: 1, max: ATTRIBUTE_MAX },
  skills: { min: 0, max: SKILL_MAX },
};

const BUDGETS: Readonly<Record<TraitKind, Readonly<Record<Rank, number>>>> = {
  attributes: ATTRIBUTE_BUDGETS,
  skills: SKILL_BUDGETS,
};

export function traitNames(kind: TraitKind, category: Category): readonly string[] {
  return kind === "attributes" ? ATTRIBUTES[category] : SKILLS[category];
}

export type TraitValues = Readonly<Record<string, number>>;

export function initialTraits(kind: TraitKind): Record<string, number> {
  const values: Record<string, number> = {};
  for (const category of CATEGORIES) {
    for (const name of traitNames(kind, category)) {
      values[name] = TRAIT_BOUNDS[kind].min;
    }
  }
  return values;
}

export const DEFAULT_PRIORITIES: Priorities = { mental: 1, physical: 2, social: 3 };

export function budget(kind: TraitKind, priorities: Priorities, category: Category): number {
  return BUDGETS[kind][priorities[category]];
}

/** Points dépensés dans une catégorie, sans compter le point gratuit des attributs. */
export function spent(kind: TraitKind, values: TraitValues, category: Category): number {
  return traitNames(kind, category).reduce(
    (total, name) => total + (values[name] ?? 0) - TRAIT_BOUNDS[kind].min,
    0,
  );
}

export function remaining(
  kind: TraitKind,
  priorities: Priorities,
  values: TraitValues,
  category: Category,
): number {
  return budget(kind, priorities, category) - spent(kind, values, category);
}

/**
 * Nouvelle valeur d'un trait après un clic sur son n-ième point (06-I2).
 *
 * Cliquer le point de la valeur actuelle la baisse d'un point. Jamais sous le
 * minimum, jamais au-delà du plafond, et jamais au-delà du budget restant de
 * la catégorie.
 */
export function clickedValue(
  kind: TraitKind,
  priorities: Priorities,
  values: TraitValues,
  category: Category,
  name: string,
  rank: number,
): number {
  const { min, max } = TRAIT_BOUNDS[kind];
  const current = values[name] ?? min;
  const wanted = Math.min(max, Math.max(min, rank === current ? rank - 1 : rank));
  const ceiling = current + remaining(kind, priorities, values, category);
  return Math.min(wanted, ceiling);
}

export interface PriorityChange {
  readonly priorities: Priorities;
  readonly values: Record<string, number>;
  /** Catégories remises à zéro parce que leur nouveau budget était dépassé (06-I1). */
  readonly trimmed: readonly Category[];
}

/**
 * Donne une priorité à une catégorie ; celle qui l'avait prend l'ancienne
 * priorité de la première (06-I1). Une catégorie dont le nouveau budget est
 * dépassé est remise à son point de départ, et signalée.
 */
export function changePriority(
  kind: TraitKind,
  priorities: Priorities,
  values: TraitValues,
  category: Category,
  rank: Rank,
): PriorityChange {
  const holder = CATEGORIES.find((other) => priorities[other] === rank);
  const next: Record<Category, Rank> = { ...priorities, [category]: rank };
  if (holder !== undefined && holder !== category) {
    next[holder] = priorities[category];
  }
  const updated: Record<string, number> = { ...values };
  const trimmed: Category[] = [];
  for (const candidate of CATEGORIES) {
    if (spent(kind, updated, candidate) > budget(kind, next, candidate)) {
      trimmed.push(candidate);
      for (const name of traitNames(kind, candidate)) {
        updated[name] = TRAIT_BOUNDS[kind].min;
      }
    }
  }
  return { priorities: next, values: updated, trimmed };
}

/** Première catégorie dont le budget n'est pas exactement dépensé, avec le reste. */
export function firstIncomplete(
  kind: TraitKind,
  priorities: Priorities,
  values: TraitValues,
): { category: Category; left: number } | null {
  for (const category of CATEGORIES) {
    const left = remaining(kind, priorities, values, category);
    if (left !== 0) {
      return { category, left };
    }
  }
  return null;
}

/** Attributs à 4 ou 5, à discuter avec le MJ (RM-002). */
export function attributesToDiscuss(values: TraitValues): AttributeName[] {
  return CATEGORIES.flatMap((category) => ATTRIBUTES[category]).filter(
    (name) => (values[name] ?? 0) >= ATTRIBUTE_ALERT_THRESHOLD,
  );
}

export interface SpecialtyDraft {
  readonly skill: SkillName | "";
  readonly label: string;
}

/** Index (à partir de 0) de la première spécialité invalide, ou `null` (RM-004). */
export function firstInvalidSpecialty(
  specialties: readonly SpecialtyDraft[],
  skills: TraitValues,
): number | null {
  const index = specialties.findIndex(
    (specialty) =>
      specialty.skill === "" ||
      (skills[specialty.skill] ?? 0) < 1 ||
      specialty.label.trim() === "" ||
      specialty.label.includes(","),
  );
  return index === -1 ? null : index;
}

export type BaseValues = Readonly<Record<EffectiveField, number>>;

/**
 * Valeurs de base (RM-006, RM-007, RM-010).
 *
 * @param size Taille retenue : la santé de base en dépend.
 */
export function baseValues(
  attributes: TraitValues,
  skills: TraitValues,
  size: number = BASE_SIZE,
): BaseValues {
  const trait = (name: string): number => attributes[name] ?? skills[name] ?? 0;
  return {
    size: BASE_SIZE,
    speed: trait("strength") + trait("dexterity") + SPEED_BONUS,
    defense: Math.min(trait("wits"), trait("dexterity")) + (skills.athletics ?? 0),
    initiative: trait("dexterity") + trait("composure"),
    health_max: size + trait("stamina"),
    willpower_max: trait("resolve") + trait("composure"),
  };
}
