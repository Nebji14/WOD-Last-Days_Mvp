import { describe, expect, it } from "vitest";

import {
  attributesToDiscuss,
  baseValues,
  changePriority,
  clickedValue,
  DEFAULT_PRIORITIES,
  firstIncomplete,
  firstInvalidSpecialty,
  initialTraits,
  remaining,
  spent,
} from "./rules";

describe("RM-001 · attributs", () => {
  it("compte le point gratuit comme non dépensé", () => {
    const values = initialTraits("attributes");
    expect(spent("attributes", values, "mental")).toBe(0);
    expect(remaining("attributes", DEFAULT_PRIORITIES, values, "mental")).toBe(5);
    expect(remaining("attributes", DEFAULT_PRIORITIES, values, "social")).toBe(3);
  });

  it("ne descend jamais sous 1 et baisse d'un point au clic sur la valeur actuelle", () => {
    const values = { ...initialTraits("attributes"), intelligence: 3 };
    expect(
      clickedValue("attributes", DEFAULT_PRIORITIES, values, "mental", "intelligence", 3),
    ).toBe(2);
    expect(
      clickedValue("attributes", DEFAULT_PRIORITIES, values, "mental", "intelligence", 1),
    ).toBe(1);
    const atOne = initialTraits("attributes");
    expect(clickedValue("attributes", DEFAULT_PRIORITIES, atOne, "mental", "intelligence", 1)).toBe(
      1,
    );
  });

  it("ne dépasse jamais le budget restant de la catégorie", () => {
    const values = { ...initialTraits("attributes"), presence: 3 };
    expect(clickedValue("attributes", DEFAULT_PRIORITIES, values, "social", "composure", 5)).toBe(
      2,
    );
  });

  it("signale la première catégorie incomplète", () => {
    const values = initialTraits("attributes");
    expect(firstIncomplete("attributes", DEFAULT_PRIORITIES, values)).toEqual({
      category: "mental",
      left: 5,
    });
  });
});

describe("06-I1 · échange de priorités", () => {
  it("échange les priorités et remet à zéro une catégorie dont le budget est dépassé", () => {
    const values = { ...initialTraits("attributes"), intelligence: 4, wits: 3 };
    const change = changePriority("attributes", DEFAULT_PRIORITIES, values, "mental", 3);
    expect(change.priorities).toEqual({ mental: 3, physical: 2, social: 1 });
    expect(change.trimmed).toEqual(["mental"]);
    expect(change.values.intelligence).toBe(1);
  });

  it("garde les points qui tiennent dans le nouveau budget", () => {
    const values = { ...initialTraits("attributes"), intelligence: 3 };
    const change = changePriority("attributes", DEFAULT_PRIORITIES, values, "mental", 2);
    expect(change.trimmed).toEqual([]);
    expect(change.values.intelligence).toBe(3);
  });
});

describe("RM-002 · alerte", () => {
  it("signale les attributs à 4 ou 5", () => {
    const values = { ...initialTraits("attributes"), strength: 4, wits: 5, resolve: 3 };
    expect(attributesToDiscuss(values)).toEqual(["wits", "strength"]);
  });
});

describe("RM-003 · compétences", () => {
  it("part de 0 avec les budgets 11 / 7 / 4", () => {
    const values = initialTraits("skills");
    expect(remaining("skills", DEFAULT_PRIORITIES, values, "mental")).toBe(11);
    expect(remaining("skills", DEFAULT_PRIORITIES, values, "social")).toBe(4);
    expect(clickedValue("skills", DEFAULT_PRIORITIES, values, "mental", "occult", 1)).toBe(1);
  });
});

describe("RM-004 · spécialités", () => {
  const skills = { ...initialTraits("skills"), firearms: 2, survival: 1 };

  it("accepte trois spécialités sur des compétences à 1 point ou plus", () => {
    const specialties = [
      { skill: "firearms", label: "Fusil" },
      { skill: "survival", label: "Pistage" },
      { skill: "firearms", label: "Pistolet" },
    ] as const;
    expect(firstInvalidSpecialty(specialties, skills)).toBeNull();
  });

  it("refuse une compétence à 0, un texte vide ou une virgule", () => {
    expect(firstInvalidSpecialty([{ skill: "occult", label: "Rituels" }], skills)).toBe(0);
    expect(firstInvalidSpecialty([{ skill: "firearms", label: " " }], skills)).toBe(0);
    expect(firstInvalidSpecialty([{ skill: "firearms", label: "Fusil, Arc" }], skills)).toBe(0);
    expect(firstInvalidSpecialty([{ skill: "", label: "Fusil" }], skills)).toBe(0);
  });
});

describe("RM-006, RM-007, RM-010 · valeurs de base", () => {
  it("applique les formules", () => {
    const attributes = {
      ...initialTraits("attributes"),
      strength: 3,
      dexterity: 2,
      stamina: 2,
      wits: 3,
      resolve: 2,
      composure: 2,
    };
    const skills = { ...initialTraits("skills"), athletics: 2 };
    expect(baseValues(attributes, skills)).toEqual({
      size: 5,
      speed: 10,
      defense: 4,
      initiative: 4,
      health_max: 7,
      willpower_max: 4,
    });
    expect(baseValues(attributes, skills, 6).health_max).toBe(8);
  });
});
