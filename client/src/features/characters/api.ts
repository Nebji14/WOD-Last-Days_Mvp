/**
 * Appels API des personnages et de leurs fiches.
 *
 * Chaque écriture renvoie le personnage à jour, que l'appelant affiche tel quel.
 */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

import {
  type Category,
  type Character,
  type Entry,
  type EntryKind,
  parseCharacter,
  type Tactic,
} from "./model";

type Method = "POST" | "PUT" | "PATCH" | "DELETE";

function write(method: Method, path: string, body?: unknown): Promise<Character> {
  return apiRequest(path, { method, body, parse: parseCharacter });
}

function parseCharacters(data: unknown): Character[] {
  if (isRecord(data) && Array.isArray(data.characters)) {
    return data.characters.map(parseCharacter);
  }
  throw new ApiError(502, "internal_error");
}

/** Mes personnages, ou ceux d'un joueur pour le MJ. */
export function fetchCharacters(ownerId?: string): Promise<Character[]> {
  const query = ownerId === undefined ? "" : `?owner=${ownerId}`;
  return apiRequest(`/api/characters${query}`, { parse: parseCharacters });
}

export function fetchCharacter(characterId: string): Promise<Character> {
  return apiRequest(`/api/characters/${characterId}`, { parse: parseCharacter });
}

export interface CreationPayload {
  readonly identity: Readonly<Record<string, string>>;
  readonly attribute_priorities: Readonly<Record<Category, number>>;
  readonly attributes: Readonly<Record<string, number>>;
  readonly skill_priorities: Readonly<Record<Category, number>>;
  readonly skills: Readonly<Record<string, number>>;
  readonly specialties: readonly { readonly skill: string; readonly label: string }[];
  readonly effective: Readonly<Record<string, number>>;
}

/** Crée un personnage depuis l'assistant. */
export function createCharacter(payload: CreationPayload): Promise<Character> {
  return write("POST", "/api/characters", payload);
}

/** Supprime définitivement un personnage. */
export function deleteCharacter(characterId: string): Promise<void> {
  return apiRequest(`/api/characters/${characterId}`, { method: "DELETE" });
}

/** Désigne le personnage joué à la table. */
export function playCharacter(characterId: string): Promise<Character> {
  return write("POST", `/api/characters/${characterId}/play`);
}

/** Déclenche l'éveil d'un personnage. Réservé au MJ, refusé par le serveur sinon. */
export function awakenCharacter(characterId: string): Promise<Character> {
  return write("POST", `/api/characters/${characterId}/awaken`);
}

/**
 * Modifie un champ, enregistré seul et aussitôt.
 *
 * @param expected valeur affichée avant la saisie : le serveur refuse l'écriture
 *   si elle a changé entre-temps.
 */
export function setSheetField(
  sheetId: string,
  field: string,
  value: string | number,
  expected: string | number,
): Promise<Character> {
  return write("PATCH", `/api/sheets/${sheetId}`, { field, value, expected });
}

export function setCharacterField(
  characterId: string,
  field: string,
  value: string | number,
  expected: string | number,
): Promise<Character> {
  return write("PATCH", `/api/characters/${characterId}`, { field, value, expected });
}

export type WoundSymbol = "*" | "X" | "/";

/** Ajoute, soigne ou aggrave une blessure. */
export function changeWounds(
  sheetId: string,
  action: "add" | "heal" | "worsen",
  wound: WoundSymbol | null,
  expected: string,
): Promise<Character> {
  return write("POST", `/api/sheets/${sheetId}/wounds`, { action, wound, expected });
}

export function addForm(characterId: string, formName: string): Promise<Character> {
  return write("POST", `/api/characters/${characterId}/forms`, { form_name: formName });
}

export function deleteForm(sheetId: string): Promise<Character> {
  return write("DELETE", `/api/sheets/${sheetId}`);
}

/** Remplace les spécialités d'une compétence ; un texte vide les supprime. */
export function setSpecialties(sheetId: string, skill: string, text: string): Promise<Character> {
  return write("PUT", `/api/sheets/${sheetId}/specialties/${skill}`, { text });
}

export function addMoralityNote(sheetId: string, level: number, body: string): Promise<Character> {
  return write("POST", `/api/sheets/${sheetId}/morality-notes`, { level, body });
}

export function updateMoralityNote(
  noteId: string,
  level: number,
  body: string,
): Promise<Character> {
  return write("PATCH", `/api/morality-notes/${noteId}`, { level, body });
}

export function deleteMoralityNote(noteId: string): Promise<Character> {
  return write("DELETE", `/api/morality-notes/${noteId}`);
}

export type EntryValues = Partial<Omit<Entry, "id" | "kind">>;

export function addEntry(
  sheetId: string,
  kind: EntryKind,
  values: EntryValues,
): Promise<Character> {
  return write("POST", `/api/sheets/${sheetId}/entries`, { kind, ...values });
}

export function updateEntry(entryId: string, values: EntryValues): Promise<Character> {
  return write("PATCH", `/api/entries/${entryId}`, values);
}

export function deleteEntry(entryId: string): Promise<Character> {
  return write("DELETE", `/api/entries/${entryId}`);
}

function parseTactics(data: unknown): Tactic[] {
  if (isRecord(data) && Array.isArray(data.tactics)) {
    return data.tactics.filter(
      (tactic): tactic is Tactic =>
        isRecord(tactic) &&
        typeof tactic.id === "string" &&
        typeof tactic.name === "string" &&
        typeof tactic.description === "string",
    );
  }
  throw new ApiError(502, "internal_error");
}

/** Tactiques existantes, pour en rattacher une à la feuille. */
export function fetchTactics(): Promise<Tactic[]> {
  return apiRequest("/api/tactics", { parse: parseTactics });
}

export function createTactic(
  sheetId: string,
  name: string,
  description: string,
): Promise<Character> {
  return write("POST", `/api/sheets/${sheetId}/tactics`, { name, description });
}

export function linkTactic(sheetId: string, tacticId: string): Promise<Character> {
  return write("POST", `/api/sheets/${sheetId}/tactics`, { tactic_id: tacticId });
}

export function updateTactic(
  sheetId: string,
  tacticId: string,
  name: string,
  description: string,
): Promise<Character> {
  return write("PATCH", `/api/sheets/${sheetId}/tactics/${tacticId}`, { name, description });
}

export function removeTactic(sheetId: string, tacticId: string): Promise<Character> {
  return write("DELETE", `/api/sheets/${sheetId}/tactics/${tacticId}`);
}

/** Enregistre une dépense d'expérience : type, points, justification obligatoire. */
export function addExpense(
  characterId: string,
  isTactical: boolean,
  points: number,
  justification: string,
): Promise<Character> {
  return write("POST", `/api/characters/${characterId}/xp-expenses`, {
    is_tactical: isTactical,
    points,
    justification,
  });
}

export function deleteExpense(expenseId: string): Promise<Character> {
  return write("DELETE", `/api/xp-expenses/${expenseId}`);
}

/** Crée une note vide et retourne son identifiant, à sélectionner. */
export function addNote(characterId: string): Promise<{ character: Character; noteId: string }> {
  return apiRequest(`/api/characters/${characterId}/notes`, {
    method: "POST",
    parse: (data) => {
      if (isRecord(data) && typeof data.note_id === "string") {
        return { character: parseCharacter(data.character), noteId: data.note_id };
      }
      throw new ApiError(502, "internal_error");
    },
  });
}

export function updateNote(noteId: string, title: string, body: string): Promise<Character> {
  return write("PATCH", `/api/notes/${noteId}`, { title, body });
}

export function deleteNote(noteId: string): Promise<Character> {
  return write("DELETE", `/api/notes/${noteId}`);
}
