/** Appels API de la musique : lecture commune, recherche, file et playlists. */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

import {
  type Deck,
  type ListedTrack,
  type NowPlaying,
  parseDeck,
  parseListedTrack,
  parseNowPlaying,
  parseTrack,
  type Playlist,
  type RepeatMode,
  type Track,
} from "./model";

/** Refuse une réponse mal formée. */
function required<T>(parse: (data: unknown) => T | null): (data: unknown) => T {
  return (data) => {
    const value = parse(data);
    if (value === null) {
      throw new ApiError(502, "internal_error");
    }
    return value;
  };
}

function parseTracks(data: unknown): readonly Track[] | null {
  if (!isRecord(data) || !Array.isArray(data.tracks)) {
    return null;
  }
  const tracks = data.tracks.map(parseTrack);
  return tracks.every((track): track is Track => track !== null) ? tracks : null;
}

function parseSuggestions(data: unknown): readonly string[] | null {
  if (!isRecord(data) || !Array.isArray(data.suggestions)) {
    return null;
  }
  return data.suggestions.filter((item): item is string => typeof item === "string");
}

function parsePlaylist(data: unknown): Playlist | null {
  if (
    !isRecord(data) ||
    typeof data.id !== "string" ||
    typeof data.name !== "string" ||
    !Array.isArray(data.tracks)
  ) {
    return null;
  }
  const tracks = data.tracks.map(parseListedTrack);
  return tracks.every((track): track is ListedTrack => track !== null)
    ? { id: data.id, name: data.name, tracks }
    : null;
}

function parsePlaylists(data: unknown): readonly Playlist[] | null {
  if (!isRecord(data) || !Array.isArray(data.playlists)) {
    return null;
  }
  const playlists = data.playlists.map(parsePlaylist);
  return playlists.every((playlist): playlist is Playlist => playlist !== null) ? playlists : null;
}

// --- Lecture ------------------------------------------------------------------------------

export function fetchNowPlaying(): Promise<NowPlaying> {
  return apiRequest("/api/music", { parse: required(parseNowPlaying) });
}

export function fetchDeck(): Promise<Deck> {
  return apiRequest("/api/music/deck", { parse: required(parseDeck) });
}

export function searchTracks(query: string): Promise<readonly Track[]> {
  const params = new URLSearchParams({ q: query });
  return apiRequest(`/api/music/search?${params.toString()}`, { parse: required(parseTracks) });
}

/** Recherches proposées pour un texte en cours de saisie. */
export function fetchSuggestions(query: string): Promise<readonly string[]> {
  const params = new URLSearchParams({ q: query });
  return apiRequest(`/api/music/suggestions?${params.toString()}`, {
    parse: required(parseSuggestions),
  });
}

export function playTrack(videoId: string, showVideo: boolean): Promise<void> {
  return apiRequest("/api/music/play", {
    method: "POST",
    body: { video_id: videoId, show_video: showVideo },
  });
}

/** Affiche ou range, chez tous, la vidéo du morceau en cours. */
export function showVideo(shown: boolean): Promise<void> {
  return apiRequest("/api/music/video", { method: "PUT", body: { shown } });
}

export function pauseMusic(): Promise<void> {
  return apiRequest("/api/music/pause", { method: "POST" });
}

export function resumeMusic(): Promise<void> {
  return apiRequest("/api/music/resume", { method: "POST" });
}

export function stopMusic(): Promise<void> {
  return apiRequest("/api/music/stop", { method: "POST" });
}

/** Passe au suivant, si la lecture visée est toujours en cours. */
export function skipTrack(playId: number): Promise<void> {
  return apiRequest("/api/music/skip", { method: "POST", body: { play_id: playId } });
}

export function seekMusic(seconds: number): Promise<void> {
  return apiRequest("/api/music/position", { method: "PUT", body: { seconds } });
}

export function setRepeat(mode: RepeatMode): Promise<void> {
  return apiRequest("/api/music/repeat", { method: "PUT", body: { mode } });
}

// --- File d'attente -----------------------------------------------------------------------

export function enqueueTrack(videoId: string): Promise<void> {
  return apiRequest("/api/music/queue", { method: "POST", body: { video_id: videoId } });
}

export function clearQueue(): Promise<void> {
  return apiRequest("/api/music/queue", { method: "DELETE" });
}

export function playQueued(itemId: string): Promise<void> {
  return apiRequest(`/api/music/queue/${itemId}/play`, { method: "POST" });
}

export function moveQueued(itemId: string, index: number): Promise<void> {
  return apiRequest(`/api/music/queue/${itemId}/index`, { method: "PUT", body: { index } });
}

export function removeQueued(itemId: string): Promise<void> {
  return apiRequest(`/api/music/queue/${itemId}`, { method: "DELETE" });
}

// --- Playlists ----------------------------------------------------------------------------

export function fetchPlaylists(): Promise<readonly Playlist[]> {
  return apiRequest("/api/playlists", { parse: required(parsePlaylists) });
}

export function createPlaylist(name: string): Promise<void> {
  return apiRequest("/api/playlists", { method: "POST", body: { name } });
}

export function renamePlaylist(playlistId: string, name: string): Promise<void> {
  return apiRequest(`/api/playlists/${playlistId}`, { method: "PATCH", body: { name } });
}

export function deletePlaylist(playlistId: string): Promise<void> {
  return apiRequest(`/api/playlists/${playlistId}`, { method: "DELETE" });
}

export function addToPlaylist(playlistId: string, videoId: string): Promise<void> {
  return apiRequest(`/api/playlists/${playlistId}/tracks`, {
    method: "POST",
    body: { video_id: videoId },
  });
}

export function removeFromPlaylist(playlistId: string, entryId: string): Promise<void> {
  return apiRequest(`/api/playlists/${playlistId}/tracks/${entryId}`, { method: "DELETE" });
}

export function playPlaylist(playlistId: string, shuffled: boolean): Promise<void> {
  return apiRequest(`/api/playlists/${playlistId}/play`, { method: "POST", body: { shuffled } });
}
