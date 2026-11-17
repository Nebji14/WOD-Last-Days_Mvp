/** Appels API et modèle du chat général. */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

export interface ChatMessage {
  readonly id: string;
  /** Rang d'envoi : fixe l'ordre d'affichage et sert de curseur d'historique. */
  readonly position: number;
  readonly author: {
    readonly id: string;
    readonly displayName: string;
    readonly role: "player" | "gm";
  };
  /** `null` pour un message supprimé. */
  readonly body: string | null;
  readonly sentAt: string;
  readonly edited: boolean;
  /** Rôle de qui a supprimé le message, `null` s'il ne l'est pas. */
  readonly deletedBy: "player" | "gm" | null;
}

export interface HistoryPage {
  /** Messages dans l'ordre chronologique. */
  readonly messages: readonly ChatMessage[];
  /** Il existe des messages plus anciens que cette page. */
  readonly hasMore: boolean;
}

export const MESSAGE_MAX_LENGTH = 2000;

function isRole(value: unknown): value is "player" | "gm" {
  return value === "player" || value === "gm";
}

/** Valide un message reçu de l'API ou du temps réel. Retourne `null` s'il est mal formé. */
export function parseMessage(data: unknown): ChatMessage | null {
  if (
    !isRecord(data) ||
    !isRecord(data.author) ||
    typeof data.id !== "string" ||
    typeof data.position !== "number" ||
    typeof data.author.id !== "string" ||
    typeof data.author.display_name !== "string" ||
    !isRole(data.author.role) ||
    (data.body !== null && typeof data.body !== "string") ||
    typeof data.sent_at !== "string" ||
    typeof data.edited !== "boolean" ||
    (data.deleted_by !== null && !isRole(data.deleted_by))
  ) {
    return null;
  }
  return {
    id: data.id,
    position: data.position,
    author: {
      id: data.author.id,
      displayName: data.author.display_name,
      role: data.author.role,
    },
    body: data.body,
    sentAt: data.sent_at,
    edited: data.edited,
    deletedBy: data.deleted_by,
  };
}

function requireMessage(data: unknown): ChatMessage {
  const message = parseMessage(data);
  if (message === null) {
    throw new ApiError(502, "internal_error");
  }
  return message;
}

function parseHistory(data: unknown): HistoryPage {
  if (!isRecord(data) || !Array.isArray(data.messages) || typeof data.has_more !== "boolean") {
    throw new ApiError(502, "internal_error");
  }
  return { messages: data.messages.map(requireMessage), hasMore: data.has_more };
}

/** Charge une page d'historique : la plus récente, ou celle qui précède `before`. */
export function fetchHistory(before?: number): Promise<HistoryPage> {
  const query = before === undefined ? "" : `?before=${before}`;
  return apiRequest(`/api/chat/messages${query}`, { parse: parseHistory });
}

/**
 * Envoie un message. Rejouer l'appel avec le même `clientToken` ne crée pas de
 * doublon : c'est ce qui permet de retenter après une coupure.
 */
export function sendMessage(clientToken: string, body: string): Promise<ChatMessage> {
  return apiRequest("/api/chat/messages", {
    method: "POST",
    body: { client_token: clientToken, body },
    parse: requireMessage,
  });
}

export function editMessage(id: string, body: string): Promise<ChatMessage> {
  return apiRequest(`/api/chat/messages/${id}`, {
    method: "PATCH",
    body: { body },
    parse: requireMessage,
  });
}

export function deleteMessage(id: string): Promise<ChatMessage> {
  return apiRequest(`/api/chat/messages/${id}`, { method: "DELETE", parse: requireMessage });
}
