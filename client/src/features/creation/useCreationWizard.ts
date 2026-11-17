"use client";

/**
 * État de l'assistant de création (écran 06, US-007).
 *
 * Tout reste dans la fenêtre jusqu'au bouton « Créer le personnage » : rien
 * n'est enregistré avant, et fermer la fenêtre abandonne la création (Q06-1).
 */
import { useReducer } from "react";

import type { CreationPayload } from "@/features/characters/api";
import type { Category, EffectiveField, SkillName } from "@/features/characters/model";

import {
  changePriority,
  clickedValue,
  DEFAULT_PRIORITIES,
  initialTraits,
  type Priorities,
  type Rank,
  SPECIALTY_COUNT,
  type SpecialtyDraft,
  type TraitKind,
} from "./rules";

export const STEPS = ["identity", "attributes", "skills", "specialties", "summary"] as const;
export type Step = (typeof STEPS)[number];

export const IDENTITY_FIELDS = [
  "name",
  "concept",
  "profession",
  "virtue",
  "vice",
  "compact",
] as const;
export type IdentityField = (typeof IDENTITY_FIELDS)[number];

export interface CreationState {
  readonly step: number;
  /** Étape la plus avancée atteinte : on peut revenir sur toute étape déjà faite. */
  readonly reached: number;
  readonly identity: Readonly<Record<IdentityField, string>>;
  readonly priorities: Readonly<Record<TraitKind, Priorities>>;
  readonly traits: Readonly<Record<TraitKind, Readonly<Record<string, number>>>>;
  readonly specialties: readonly SpecialtyDraft[];
  /** Valeurs effectives saisies à l'étape 5 ; absentes, elles reprennent la base. */
  readonly effective: Readonly<Partial<Record<EffectiveField, number>>>;
  /** Catégories vidées par le dernier échange de priorités (06-I1). */
  readonly trimmed: readonly Category[];
  /** Vrai dès la première saisie : fermer demande alors confirmation. */
  readonly dirty: boolean;
}

export type CreationAction =
  | { readonly type: "identity"; readonly field: IdentityField; readonly value: string }
  | {
      readonly type: "priority";
      readonly kind: TraitKind;
      readonly category: Category;
      readonly rank: Rank;
    }
  | {
      readonly type: "trait";
      readonly kind: TraitKind;
      readonly category: Category;
      readonly name: string;
      readonly rank: number;
    }
  | { readonly type: "specialty"; readonly index: number; readonly value: SpecialtyDraft }
  | { readonly type: "effective"; readonly field: EffectiveField; readonly value: number }
  | { readonly type: "goto"; readonly step: number };

function initialState(): CreationState {
  return {
    step: 0,
    reached: 0,
    identity: { name: "", concept: "", profession: "", virtue: "", vice: "", compact: "" },
    priorities: { attributes: DEFAULT_PRIORITIES, skills: DEFAULT_PRIORITIES },
    traits: { attributes: initialTraits("attributes"), skills: initialTraits("skills") },
    specialties: Array.from({ length: SPECIALTY_COUNT }, () => ({ skill: "", label: "" })),
    effective: {},
    trimmed: [],
    dirty: false,
  };
}

function edited(state: CreationState, patch: Partial<CreationState>): CreationState {
  return { ...state, trimmed: [], ...patch, dirty: true };
}

export function creationReducer(state: CreationState, action: CreationAction): CreationState {
  switch (action.type) {
    case "identity":
      return edited(state, { identity: { ...state.identity, [action.field]: action.value } });
    case "priority": {
      const { kind } = action;
      const change = changePriority(
        kind,
        state.priorities[kind],
        state.traits[kind],
        action.category,
        action.rank,
      );
      return edited(state, {
        priorities: { ...state.priorities, [kind]: change.priorities },
        traits: { ...state.traits, [kind]: change.values },
        trimmed: change.trimmed,
      });
    }
    case "trait": {
      const { kind } = action;
      const values = state.traits[kind];
      const value = clickedValue(
        kind,
        state.priorities[kind],
        values,
        action.category,
        action.name,
        action.rank,
      );
      return edited(state, {
        traits: { ...state.traits, [kind]: { ...values, [action.name]: value } },
      });
    }
    case "specialty":
      return edited(state, {
        specialties: state.specialties.map((specialty, index) =>
          index === action.index ? action.value : specialty,
        ),
      });
    case "effective":
      return edited(state, { effective: { ...state.effective, [action.field]: action.value } });
    case "goto":
      if (action.step < 0 || action.step > Math.min(state.reached + 1, STEPS.length - 1)) {
        return state;
      }
      return {
        ...state,
        step: action.step,
        reached: Math.max(state.reached, action.step),
        trimmed: [],
      };
  }
}

export function useCreationWizard() {
  return useReducer(creationReducer, undefined, initialState);
}

/** Saisie envoyée au serveur, qui refait tous les contrôles (US-007 · CA2). */
export function toPayload(state: CreationState): CreationPayload {
  return {
    identity: Object.fromEntries(
      IDENTITY_FIELDS.map((field) => [field, state.identity[field].trim()]),
    ),
    attribute_priorities: state.priorities.attributes,
    attributes: state.traits.attributes,
    skill_priorities: state.priorities.skills,
    skills: state.traits.skills,
    specialties: state.specialties.map((specialty) => ({
      skill: specialty.skill as SkillName,
      label: specialty.label.trim(),
    })),
    effective: state.effective,
  };
}
