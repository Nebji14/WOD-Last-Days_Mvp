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

export function sheetPath(characterId: string): string {
  return `/fiche/${characterId}`;
}
export const CREATION_PATH = "/creation";
export const PROFILE_PATH = "/profil";

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

export function openSheet(characterId: string): void {
  openDetached(`hunter-fiche-${characterId}`, sheetPath(characterId), SHEET_WINDOW);
}

export function openCreation(): void {
  openDetached("hunter-creation", CREATION_PATH, CREATION_WINDOW);
}

export function openProfile(): void {
  openDetached("hunter-profil", PROFILE_PATH, PROFILE_WINDOW);
}

/** Ferme toutes les fenêtres détachées ouvertes depuis cette fenêtre (T3). */
export function closeAllDetached(): void {
  opened.forEach((detached) => detached.close());
  opened.clear();
}
