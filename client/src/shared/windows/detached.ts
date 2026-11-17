/**
 * Fenêtres détachables (règle T2).
 *
 * Fiche, création et profil s'ouvrent dans une vraie fenêtre du navigateur,
 * que l'utilisateur peut déplacer sur un autre écran : jamais dans une fenêtre
 * modale dessinée dans la page. Une fenêtre par outil et une par fiche : rouvrir
 * une fenêtre déjà ouverte la ramène au premier plan.
 *
 * La fenêtre principale garde la trace de celles qu'elle a ouvertes pour les
 * fermer quand elle se ferme ou à la déconnexion (règle T3).
 */
const opened = new Map<string, Window>();

interface WindowSize {
  readonly width: number;
  readonly height: number;
}

/** Tailles des cadres de la maquette, bornées à l'écran disponible à l'ouverture. */
export const SHEET_WINDOW: WindowSize = { width: 1200, height: 900 };
export const CREATION_WINDOW: WindowSize = { width: 1200, height: 760 };
export const PROFILE_WINDOW: WindowSize = { width: 1200, height: 800 };
export const TOOL_WINDOW: WindowSize = { width: 1200, height: 800 };

export function sheetPath(characterId: string): string {
  return `/fiche/${characterId}`;
}
export const CREATION_PATH = "/creation";
export const PROFILE_PATH = "/profil";
export const PLAYERS_TOOL_PATH = "/outils/joueurs";
export const IMAGES_TOOL_PATH = "/outils/images";
/** Paramètre d'adresse qui ouvre une fiche directement en mode modification (04a-I3). */
export const EDIT_MODE_PARAM = "mode";
export const EDIT_MODE_VALUE = "modification";

/**
 * Ouvre une fenêtre détachée, ou ramène au premier plan celle qui porte déjà ce nom.
 *
 * @param name nom unique de la fenêtre : un par outil, un par fiche.
 * @param path adresse de la page à afficher, sur la même origine.
 */
export function openDetached(name: string, path: string, size: WindowSize): void {
  const existing = opened.get(name);
  if (existing && !existing.closed) {
    existing.focus();
    return;
  }
  const width = Math.min(size.width, window.screen.availWidth);
  const height = Math.min(size.height, window.screen.availHeight);
  const detached = window.open(path, name, `popup=yes,width=${width},height=${height}`);
  if (detached) {
    opened.set(name, detached);
  }
}

/** Nom de la fenêtre d'une fiche : un seul nom par personnage (T2). */
export function sheetWindowName(characterId: string): string {
  return `hunter-fiche-${characterId}`;
}

/**
 * Ouvre la fiche d'un personnage.
 *
 * @param editing ouvre la fiche en mode modification (04a-I3). Une fiche déjà
 *   ouverte est seulement ramenée au premier plan.
 */
export function openSheet(characterId: string, editing = false): void {
  const path = editing
    ? `${sheetPath(characterId)}?${EDIT_MODE_PARAM}=${EDIT_MODE_VALUE}`
    : sheetPath(characterId);
  openDetached(sheetWindowName(characterId), path, SHEET_WINDOW);
}

export function openCreation(): void {
  openDetached("hunter-creation", CREATION_PATH, CREATION_WINDOW);
}

export function openProfile(): void {
  openDetached("hunter-profil", PROFILE_PATH, PROFILE_WINDOW);
}

/** Outil Joueurs du MJ (04a) : une fenêtre par outil (T2). */
export function openPlayersTool(): void {
  openDetached("hunter-outil-joueurs", PLAYERS_TOOL_PATH, TOOL_WINDOW);
}

/** Outil Images du MJ (04b). */
export function openImagesTool(): void {
  openDetached("hunter-outil-images", IMAGES_TOOL_PATH, TOOL_WINDOW);
}

/** Ferme toutes les fenêtres détachées ouvertes depuis cette fenêtre (T3). */
export function closeAllDetached(): void {
  opened.forEach((detached) => detached.close());
  opened.clear();
}
