/** Volume personnel, retenu par le navigateur d'une séance à l'autre. */
const STORAGE_KEY = "hunter:music-volume";
const DEFAULT_VOLUME = 50;

export function readVolume(): number {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    const volume = stored === null ? DEFAULT_VOLUME : Number(stored);
    return volume >= 0 && volume <= 100 ? volume : DEFAULT_VOLUME;
  } catch {
    // Stockage bloqué par le navigateur : le volume par défaut convient.
    return DEFAULT_VOLUME;
  }
}

export function saveVolume(volume: number): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, String(volume));
  } catch (error) {
    console.warn("Volume non retenu", error);
  }
}
