/** Appels API de l'outil Joueurs du MJ. */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

export interface Player {
  readonly id: string;
  readonly username: string;
  readonly displayName: string;
  readonly status: "active" | "disabled";
  /** Connecté à la table. */
  readonly online: boolean;
  /** Noms de ses personnages, du plus ancien au plus récent. */
  readonly characterNames: readonly string[];
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

/** Valide la forme d'un joueur renvoyé par l'API. */
export function parsePlayer(data: unknown): Player {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.username === "string" &&
    typeof data.display_name === "string" &&
    (data.status === "active" || data.status === "disabled") &&
    typeof data.online === "boolean" &&
    isStringArray(data.character_names)
  ) {
    return {
      id: data.id,
      username: data.username,
      displayName: data.display_name,
      status: data.status,
      online: data.online,
      characterNames: data.character_names,
    };
  }
  throw new ApiError(502, "internal_error");
}

function parsePlayers(data: unknown): Player[] {
  if (isRecord(data) && Array.isArray(data.players)) {
    return data.players.map(parsePlayer);
  }
  throw new ApiError(502, "internal_error");
}

/** Rend son accès à un joueur qui avait désactivé son compte. */
export function reactivatePlayer(playerId: string): Promise<void> {
  return apiRequest(`/api/players/${playerId}/reactivate`, { method: "POST" });
}

/** Tous les joueurs, connectés d'abord. */
export function fetchPlayers(): Promise<Player[]> {
  return apiRequest("/api/players", { parse: parsePlayers });
}
