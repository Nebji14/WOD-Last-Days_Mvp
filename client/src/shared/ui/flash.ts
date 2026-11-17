/**
 * Notification à afficher une seule fois sur la page suivante (par exemple
 * « Déconnexion réussie » à l'arrivée sur l'écran de connexion).
 *
 * Le message survit à un rechargement complet grâce à `sessionStorage` et il
 * est consommé à sa première lecture.
 */
const STORAGE_KEY = "hunter:flash";
const FLASH_KINDS = ["loggedOut", "registered"] as const;

export type FlashKind = (typeof FLASH_KINDS)[number];

/** `undefined` : pas encore lu dans le stockage ; `null` : rien à afficher. */
let current: FlashKind | null | undefined;
const listeners = new Set<() => void>();

function isFlashKind(value: string | null): value is FlashKind {
  return FLASH_KINDS.some((kind) => kind === value);
}

/** Programme une notification pour la prochaine page affichée. */
export function setFlashForNextPage(kind: FlashKind): void {
  window.sessionStorage.setItem(STORAGE_KEY, kind);
  current = undefined;
}

/** Retourne la notification en attente et la retire du stockage. */
export function readFlash(): FlashKind | null {
  if (current === undefined) {
    const stored = window.sessionStorage.getItem(STORAGE_KEY);
    window.sessionStorage.removeItem(STORAGE_KEY);
    current = isFlashKind(stored) ? stored : null;
  }
  return current;
}

export function dismissFlash(): void {
  current = null;
  listeners.forEach((listener) => listener());
}

export function subscribeToFlash(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
