/**
 * Synchronisation de la musique : le serveur fait foi sur la position.
 *
 * Un lecteur en retard (publicité, chargement, arrivée tardive) est recalé ; un
 * petit écart est toléré pour ne pas hacher le son.
 */
import type { HeardMusic } from "./model";

const TOLERANCE_SECONDS = 2;

/** Position attendue en secondes, à l'instant `clock` de `performance.now()`. */
export function expectedPosition(heard: HeardMusic, clock: number): number {
  const { now, receivedAt } = heard;
  if (now.track === null) {
    return 0;
  }
  const elapsed = now.playing ? Math.max(0, clock - receivedAt) / 1000 : 0;
  return Math.min(now.position + elapsed, now.track.durationSeconds);
}

/** Indique si l'écart avec la position attendue s'entend. */
export function needsSeek(actual: number, expected: number): boolean {
  return Math.abs(actual - expected) > TOLERANCE_SECONDS;
}

/** Durée lisible : `4:07`, ou `1:02:09` au-delà d'une heure. */
export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const rest = String(total % 60).padStart(2, "0");
  return hours > 0
    ? `${hours}:${String(minutes).padStart(2, "0")}:${rest}`
    : `${minutes}:${rest}`;
}
