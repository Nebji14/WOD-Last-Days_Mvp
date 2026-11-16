/** Ticket d'ouverture de la connexion temps réel et adresse du serveur. */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

/** Adresse du point d'entrée WebSocket, d'après `NEXT_PUBLIC_REALTIME_URL`. */
export function realtimeUrl(): string {
  return `${process.env.NEXT_PUBLIC_REALTIME_URL ?? ""}/ws`;
}

function parseTicket(data: unknown): string {
  if (isRecord(data) && typeof data.ticket === "string") {
    return data.ticket;
  }
  throw new ApiError(502, "internal_error");
}

/**
 * Demande un ticket à usage unique. La session est renouvelée au passage si
 * elle a expiré.
 *
 * @throws {ApiError} statut 401 si la session est fermée.
 */
export function fetchRealtimeTicket(): Promise<string> {
  return apiRequest("/api/realtime/ticket", { method: "POST", parse: parseTicket });
}
