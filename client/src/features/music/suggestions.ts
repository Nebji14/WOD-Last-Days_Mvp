/**
 * Suggestions de recherche : recherches récentes, ambiances de jeu et morceaux
 * des playlists, complétés par les noms que propose le serveur.
 */
const MAX_SUGGESTIONS = 10;
const MAX_RECENT = 20;
const STORAGE_KEY = "hunter:music-recent";

/** Texte sans accents ni majuscules, pour comparer. */
function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

/** Chaque mot saisi commence un mot du texte proposé. */
export function matches(candidate: string, query: string): boolean {
  const words = normalize(candidate).split(/[^\p{Letter}\p{Number}]+/u);
  return normalize(query)
    .split(/[^\p{Letter}\p{Number}]+/u)
    .filter(Boolean)
    .every((part) => words.some((word) => word.startsWith(part)));
}

/** Un lien se colle en entier : il n'appelle aucune suggestion. */
export function isLink(query: string): boolean {
  return /:\/\/|^(www\.|m\.|music\.)?(youtube\.com|youtu\.be)\b/i.test(query.trim());
}

interface SuggestionSources {
  readonly recent: readonly string[];
  readonly ambiances: readonly string[];
  readonly playlistTitles: readonly string[];
  /** Réponse du serveur et texte auquel elle répond. */
  readonly remote: { readonly query: string; readonly items: readonly string[] };
}

/** Propose des recherches pour le texte saisi ; un champ vide montre les plus récentes. */
export function buildSuggestions(query: string, sources: SuggestionSources): readonly string[] {
  const wanted = query.trim();
  if (isLink(wanted)) {
    return [];
  }
  const local =
    wanted === ""
      ? [...sources.recent, ...sources.ambiances]
      : [...sources.recent, ...sources.ambiances, ...sources.playlistTitles].filter((item) =>
          matches(item, wanted),
        );
  // Pendant l'attente, la réponse au texte précédent sert encore si elle correspond.
  const remote =
    sources.remote.query === wanted
      ? sources.remote.items
      : sources.remote.items.filter((item) => wanted !== "" && matches(item, wanted));
  const unique = new Map<string, string>();
  // Les noms du serveur gardent toujours une place à côté des propositions locales.
  for (const item of [...local.slice(0, wanted === "" ? MAX_SUGGESTIONS : 4), ...remote]) {
    const key = normalize(item);
    if (key !== normalize(wanted) && !unique.has(key)) {
      unique.set(key, item);
    }
  }
  return [...unique.values()].slice(0, MAX_SUGGESTIONS);
}

/** Place une recherche en tête des récentes, sans doublon. */
export function withRecent(recent: readonly string[], query: string): readonly string[] {
  const key = normalize(query);
  return [query, ...recent.filter((item) => normalize(item) !== key)].slice(0, MAX_RECENT);
}

export function readRecent(): readonly string[] {
  try {
    const stored: unknown = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(stored)
      ? stored.filter((item): item is string => typeof item === "string").slice(0, MAX_RECENT)
      : [];
  } catch {
    // Stockage bloqué ou illisible : on repart sans recherches récentes.
    return [];
  }
}

export function saveRecent(recent: readonly string[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(recent));
  } catch (error) {
    console.warn("Recherches récentes non retenues", error);
  }
}
