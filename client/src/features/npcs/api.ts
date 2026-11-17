/** Appels API de l'outil PNJ (04c) et des données propres au PNJ (07). */
import { type Character, type NpcModel, parseCharacter } from "@/features/characters/model";
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

export interface NpcCategory {
  readonly id: string;
  readonly name: string;
  readonly parentId: string | null;
}

/** Carte « PNJ — … » (04c). */
export interface NpcCard {
  readonly id: string;
  readonly name: string;
  readonly concept: string;
  readonly model: NpcModel;
  readonly categoryId: string | null;
  readonly healthMax: number;
  readonly willpowerMax: number;
  readonly power: number | null;
  readonly finesse: number | null;
  readonly resilience: number | null;
}

export interface NpcDirectory {
  readonly categories: readonly NpcCategory[];
  readonly npcs: readonly NpcCard[];
}

/** Données propres au PNJ modifiables par `setNpcField` (07-I2, I4 ; Q04c-1). */
export type NpcField = "category_id" | "notes" | "power" | "finesse" | "resilience";

const invalid = (): ApiError => new ApiError(502, "internal_error");
const isNullableString = (value: unknown): value is string | null =>
  value === null || typeof value === "string";
const isNullableNumber = (value: unknown): value is number | null =>
  value === null || typeof value === "number";

function parseCategory(data: unknown): NpcCategory {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.name === "string" &&
    isNullableString(data.parent_id)
  ) {
    return { id: data.id, name: data.name, parentId: data.parent_id };
  }
  throw invalid();
}

function parseCard(data: unknown): NpcCard {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.name === "string" &&
    typeof data.concept === "string" &&
    (data.model === "full" || data.model === "simplified") &&
    isNullableString(data.category_id) &&
    typeof data.health_max === "number" &&
    typeof data.willpower_max === "number" &&
    isNullableNumber(data.power) &&
    isNullableNumber(data.finesse) &&
    isNullableNumber(data.resilience)
  ) {
    return {
      id: data.id,
      name: data.name,
      concept: data.concept,
      model: data.model,
      categoryId: data.category_id,
      healthMax: data.health_max,
      willpowerMax: data.willpower_max,
      power: data.power,
      finesse: data.finesse,
      resilience: data.resilience,
    };
  }
  throw invalid();
}

export function parseDirectory(data: unknown): NpcDirectory {
  if (isRecord(data) && Array.isArray(data.categories) && Array.isArray(data.npcs)) {
    return { categories: data.categories.map(parseCategory), npcs: data.npcs.map(parseCard) };
  }
  throw invalid();
}

function parseCreated(data: unknown): string {
  if (isRecord(data) && typeof data.id === "string") {
    return data.id;
  }
  throw invalid();
}

export function fetchDirectory(): Promise<NpcDirectory> {
  return apiRequest("/api/npcs", { parse: parseDirectory });
}

/** Crée une feuille de PNJ vierge du modèle choisi (04c-I3, RM-021). */
export function createNpc(model: NpcModel, categoryId: string | null): Promise<Character> {
  return apiRequest("/api/npcs", {
    method: "POST",
    body: { model, category_id: categoryId },
    parse: parseCharacter,
  });
}

/**
 * Modifie une donnée propre au PNJ.
 *
 * @param expected valeur affichée avant la saisie (05-E3) ; ignorée pour la catégorie.
 */
export function setNpcField(
  npcId: string,
  field: NpcField,
  value: string | number | null,
  expected: string | number | null,
): Promise<Character> {
  return apiRequest(`/api/npcs/${npcId}`, {
    method: "PATCH",
    body: { field, value, expected },
    parse: parseCharacter,
  });
}

/** Supprime définitivement la feuille du PNJ (US-043). */
export function deleteNpc(npcId: string): Promise<void> {
  return apiRequest(`/api/npcs/${npcId}`, { method: "DELETE" });
}

export function createCategory(name: string, parentId: string | null): Promise<string> {
  return apiRequest("/api/npc-categories", {
    method: "POST",
    body: { name, parent_id: parentId },
    parse: parseCreated,
  });
}

export function renameCategory(categoryId: string, name: string): Promise<void> {
  return apiRequest(`/api/npc-categories/${categoryId}`, { method: "PATCH", body: { name } });
}

export function deleteCategory(categoryId: string): Promise<void> {
  return apiRequest(`/api/npc-categories/${categoryId}`, { method: "DELETE" });
}
