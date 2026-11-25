/** Types de la musique et validation des données reçues du serveur. */
import { isRecord } from "@/shared/api/client";

export interface Track {
  readonly videoId: string;
  readonly title: string;
  readonly channel: string;
  readonly durationSeconds: number;
}

/** Lecture en cours, la même pour tous. */
export interface NowPlaying {
  /** Change à chaque lancement, même du même morceau. */
  readonly playId: number;
  readonly track: Track | null;
  readonly playing: boolean;
  /** Position en secondes quand le serveur a produit l'état. */
  readonly position: number;
  /** Vidéo affichée en grand chez tous. */
  readonly videoShown: boolean;
}

/** Lecture en cours et instant de sa réception, pour en déduire la position actuelle. */
export interface HeardMusic {
  readonly now: NowPlaying;
  /** Horloge `performance.now()` à la réception. */
  readonly receivedAt: number;
}

/** Morceau d'une file ou d'une playlist, avec son identifiant propre. */
export interface ListedTrack {
  readonly id: string;
  readonly track: Track;
}

export const REPEAT_MODES = ["off", "track", "queue"] as const;
export type RepeatMode = (typeof REPEAT_MODES)[number];

export interface Deck {
  readonly now: NowPlaying;
  readonly queue: readonly ListedTrack[];
  readonly repeat: RepeatMode;
}

export interface Playlist {
  readonly id: string;
  readonly name: string;
  readonly tracks: readonly ListedTrack[];
}

export function parseTrack(data: unknown): Track | null {
  if (
    isRecord(data) &&
    typeof data.video_id === "string" &&
    typeof data.title === "string" &&
    typeof data.channel === "string" &&
    typeof data.duration_seconds === "number"
  ) {
    return {
      videoId: data.video_id,
      title: data.title,
      channel: data.channel,
      durationSeconds: data.duration_seconds,
    };
  }
  return null;
}

export function parseNowPlaying(data: unknown): NowPlaying | null {
  if (
    !isRecord(data) ||
    typeof data.play_id !== "number" ||
    typeof data.playing !== "boolean" ||
    typeof data.position !== "number" ||
    typeof data.video_shown !== "boolean"
  ) {
    return null;
  }
  const track = data.track === null ? null : parseTrack(data.track);
  if (data.track !== null && track === null) {
    return null;
  }
  return {
    playId: data.play_id,
    track,
    playing: data.playing,
    position: data.position,
    videoShown: data.video_shown,
  };
}

export function parseListedTrack(data: unknown): ListedTrack | null {
  if (!isRecord(data) || typeof data.id !== "string") {
    return null;
  }
  const track = parseTrack(data.track);
  return track === null ? null : { id: data.id, track };
}

export function parseDeck(data: unknown): Deck | null {
  if (!isRecord(data) || !Array.isArray(data.queue)) {
    return null;
  }
  const now = parseNowPlaying(data.now);
  const repeat = REPEAT_MODES.find((mode) => mode === data.repeat);
  const queue = data.queue.map(parseListedTrack);
  if (
    now === null ||
    repeat === undefined ||
    !queue.every((item): item is ListedTrack => item !== null)
  ) {
    return null;
  }
  return { now, queue, repeat };
}
