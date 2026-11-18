/**
 * Aperçu de la réserve avant le jet, calculé comme le fait le serveur.
 *
 * Le serveur recompose la réserve lui-même : cet aperçu sert seulement à
 * montrer au joueur ce qu'il va lancer.
 */
import {
  ATTRIBUTES,
  type AttributeName,
  type Character,
  type Entry,
  type Sheet,
  SKILLS,
  type SkillName,
} from "@/features/characters/model";
import { woundPenalty } from "@/features/sheet/health";

import type { RollPart } from "./model";

export const MODIFIER_MIN = -10;
export const MODIFIER_MAX = 5;
const SPECIALTY_BONUS = 1;
const WILLPOWER_BONUS = 3;

export type NpcTrait = "power" | "finesse" | "resilience";

/** Ce que le joueur a choisi sur la fiche. */
export interface RollChoice {
  readonly attribute: AttributeName | null;
  /** Compétence ou second attribut. */
  readonly second: AttributeName | SkillName | null;
  readonly trait: NpcTrait | null;
  readonly specialty: boolean;
  readonly willpower: boolean;
  readonly modifier: number;
  readonly again: 8 | 9 | 10;
  readonly rote: boolean;
  readonly secret: boolean;
}

export const EMPTY_CHOICE: RollChoice = {
  attribute: null,
  second: null,
  trait: null,
  specialty: false,
  willpower: false,
  modifier: 0,
  again: 10,
  rote: false,
  secret: false,
};

const ATTRIBUTE_LIST: readonly string[] = Object.values(ATTRIBUTES).flat();

export function isAttribute(name: string): name is AttributeName {
  return ATTRIBUTE_LIST.includes(name);
}

/** Malus d'une compétence à 0 : −3 mentale, −1 physique ou sociale. */
export function unskilledPenalty(skill: SkillName): number {
  return (SKILLS.mental as readonly string[]).includes(skill) ? -3 : -1;
}

/** La spécialité se coche seulement sur une compétence qui en porte une. */
export function canUseSpecialty(sheet: Sheet, second: RollChoice["second"]): boolean {
  return second !== null && !isAttribute(second) && (sheet.specialties[second]?.length ?? 0) > 0;
}

/** Volonté, blessures et modificateur, comme le serveur les ajoute. */
export function bonusParts(choice: RollChoice, penalty: number): RollPart[] {
  const parts: RollPart[] = [];
  if (choice.willpower) {
    parts.push({ key: "willpower", value: WILLPOWER_BONUS });
  }
  if (penalty !== 0) {
    parts.push({ key: "wounds", value: penalty });
  }
  if (choice.modifier !== 0) {
    parts.push({ key: "modifier", value: choice.modifier });
  }
  return parts;
}

/** Composition du jet choisi ; vide tant que rien n'est sélectionné. */
export function previewParts(character: Character, sheet: Sheet, choice: RollChoice): RollPart[] {
  const penalty = woundPenalty(sheet.wound_track, sheet.effective.health_max);
  if (choice.trait !== null) {
    const value = character.npc?.[choice.trait] ?? 0;
    return [{ key: choice.trait, value }, ...bonusParts(choice, penalty)];
  }
  if (choice.attribute === null) {
    return [];
  }
  const parts: RollPart[] = [{ key: choice.attribute, value: sheet.attributes[choice.attribute] }];
  const second = choice.second;
  if (second !== null) {
    const value = isAttribute(second) ? sheet.attributes[second] : sheet.skills[second];
    parts.push({ key: second, value });
    if (!isAttribute(second) && value === 0) {
      parts.push({ key: "unskilled", value: unskilledPenalty(second) });
    }
  }
  if (choice.specialty && canUseSpecialty(sheet, second)) {
    parts.push({ key: "specialty", value: SPECIALTY_BONUS });
  }
  return [...parts, ...bonusParts(choice, penalty)];
}

/**
 * Sélection après un clic sur un trait : le premier attribut, puis la
 * compétence ou le second attribut ; un nouveau clic sur un trait choisi le retire.
 */
export function pickTrait(choice: RollChoice, name: AttributeName | SkillName): RollChoice {
  if (choice.attribute === name) {
    return { ...choice, attribute: null, specialty: false };
  }
  if (choice.second === name) {
    return { ...choice, second: null, specialty: false };
  }
  if (choice.attribute === null && isAttribute(name)) {
    return { ...choice, attribute: name, trait: null };
  }
  return { ...choice, second: name, trait: null, specialty: false };
}

/** Traits proposés hors attributs et compétences. */
export const SPECIAL_PARTS = ["supernatural", "entry_level", "weapon_bonus"] as const;

/** Réserve d'un pouvoir, d'une arme ou d'un atout, avec le malus ou bonus du MJ. */
export function recipeParts(
  character: Character,
  sheet: Sheet,
  entry: Entry,
  modifier: number,
): RollPart[] {
  const recipe = entry.roll;
  if (recipe == null) {
    return [];
  }
  const parts: RollPart[] = [];
  for (const key of recipe.parts) {
    if (key === "supernatural") {
      parts.push({ key, value: character.supernatural_level });
    } else if (key === "entry_level") {
      parts.push({ key, value: entry.level ?? 0 });
    } else if (key === "weapon_bonus") {
      parts.push({ key, value: entry.damage_modifier ?? 0 });
    } else if (isAttribute(key)) {
      parts.push({ key, value: sheet.attributes[key] });
    } else {
      const value = sheet.skills[key as SkillName];
      parts.push({ key, value });
      if (value === 0) {
        parts.push({ key: "unskilled", value: unskilledPenalty(key as SkillName) });
      }
    }
  }
  if (recipe.bonus !== 0) {
    parts.push({ key: "bonus", value: recipe.bonus });
  }
  const penalty = woundPenalty(sheet.wound_track, sheet.effective.health_max);
  return [...parts, ...bonusParts({ ...EMPTY_CHOICE, modifier }, penalty)];
}
