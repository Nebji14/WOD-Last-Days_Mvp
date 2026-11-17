import { describe, expect, it } from "vitest";

import { stepBlocker } from "./blockers";
import { type CreationAction, creationReducer, type CreationState } from "./useCreationWizard";

function start(): CreationState {
  return creationReducer(
    {
      step: 0,
      reached: 0,
      identity: { name: "", concept: "", profession: "", virtue: "", vice: "", compact: "" },
      priorities: {
        attributes: { mental: 1, physical: 2, social: 3 },
        skills: { mental: 1, physical: 2, social: 3 },
      },
      traits: {
        attributes: {
          intelligence: 1,
          wits: 1,
          resolve: 1,
          strength: 1,
          dexterity: 1,
          stamina: 1,
          presence: 1,
          manipulation: 1,
          composure: 1,
        },
        skills: {},
      },
      specialties: [
        { skill: "", label: "" },
        { skill: "", label: "" },
        { skill: "", label: "" },
      ],
      effective: {},
      trimmed: [],
      dirty: false,
    },
    { type: "goto", step: 0 },
  );
}

function apply(state: CreationState, ...actions: CreationAction[]): CreationState {
  return actions.reduce(creationReducer, state);
}

describe("assistant de création (US-007 · CA2, CA3)", () => {
  it("bloque l'identité tant que le nom est vide (06-É1)", () => {
    expect(stepBlocker(start())).not.toBeNull();
    const named = apply(start(), { type: "identity", field: "name", value: "Isaac" });
    expect(stepBlocker(named)).toBeNull();
    expect(named.dirty).toBe(true);
  });

  it("n'autorise pas de sauter une étape non atteinte", () => {
    const state = apply(start(), { type: "goto", step: 3 });
    expect(state.step).toBe(0);
    const next = apply(start(), { type: "goto", step: 1 });
    expect(next.step).toBe(1);
    expect(next.reached).toBe(1);
  });

  it("indique les points restants d'une catégorie d'attributs (06-I3)", () => {
    const state = apply(start(), { type: "goto", step: 1 });
    expect(stepBlocker(state)).toContain("5");
  });

  it("signale les catégories vidées par un échange de priorités (06-I1)", () => {
    const state = apply(
      start(),
      { type: "trait", kind: "attributes", category: "mental", name: "intelligence", rank: 5 },
      { type: "priority", kind: "attributes", category: "mental", rank: 3 },
    );
    expect(state.trimmed).toEqual(["mental"]);
    expect(state.traits.attributes.intelligence).toBe(1);
  });
});
