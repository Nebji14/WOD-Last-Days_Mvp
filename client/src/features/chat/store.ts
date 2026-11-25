/**
 * État du chat général : messages connus, historique et envois en attente.
 *
 * Un envoi est d'abord placé en attente, puis transmis. Si le réseau est
 * coupé, il reste en attente et repart seul au retour de la connexion, sans
 * ressaisie ni doublon.
 */
import { create } from "zustand";

import { ApiError } from "@/shared/api/client";

import { type ChatMessage, fetchHistory, sendMessage } from "./api";

export interface PendingMessage {
  /** Jeton d'envoi, rejoué à l'identique à chaque tentative. */
  readonly clientToken: string;
  readonly body: string;
  /** Code de l'erreur qui a définitivement refusé l'envoi, `null` s'il est en attente. */
  readonly errorCode: string | null;
}

interface ChatState {
  /** Messages connus, dans l'ordre chronologique. */
  readonly messages: readonly ChatMessage[];
  readonly hasMore: boolean;
  readonly loadingOlder: boolean;
  readonly pending: readonly PendingMessage[];
  /** Ajoute un message ou remplace sa version précédente (création, modification, suppression). */
  upsert(message: ChatMessage): void;
  /** Affiche le nouveau nom d'un participant sur ses messages. */
  renameAuthor(authorId: string, displayName: string): void;
  /** Recharge les messages les plus récents ; appelé à chaque (re)connexion. */
  loadLatest(): Promise<void>;
  /** Charge la page qui précède le plus ancien message connu. */
  loadOlder(): Promise<void>;
  /** Place un message en attente et tente de l'envoyer. */
  send(body: string): void;
  /** Tente d'envoyer tous les messages en attente, dans l'ordre. */
  flushPending(): Promise<void>;
  /** Abandonne un envoi refusé. */
  discardPending(clientToken: string): void;
  reset(): void;
}

let flushing = false;

function byPosition(a: ChatMessage, b: ChatMessage): number {
  return a.position - b.position;
}

/** Fusionne deux listes de messages ; à identifiant égal, `incoming` l'emporte. */
function merge(known: readonly ChatMessage[], incoming: readonly ChatMessage[]): ChatMessage[] {
  const byId = new Map(known.map((message) => [message.id, message]));
  incoming.forEach((message) => byId.set(message.id, message));
  return [...byId.values()].sort(byPosition);
}

export const useChatStore = create<ChatState>()((set, get) => ({
  messages: [],
  hasMore: false,
  loadingOlder: false,
  pending: [],

  upsert(message) {
    set((state) => ({ messages: merge(state.messages, [message]) }));
  },

  renameAuthor(authorId, displayName) {
    set((state) => ({
      messages: state.messages.map((message) =>
        message.author.id === authorId
          ? { ...message, author: { ...message.author, displayName } }
          : message,
      ),
    }));
  },

  async loadLatest() {
    const page = await fetchHistory();
    set((state) => {
      const newestKnown = state.messages.at(-1)?.position ?? 0;
      const oldestLoaded = page.messages[0]?.position ?? 0;
      // Trop de messages manqués pour raccorder les deux listes : on repart de la page récente.
      const disjoint = state.messages.length > 0 && page.hasMore && oldestLoaded > newestKnown;
      return disjoint || state.messages.length === 0
        ? { messages: [...page.messages], hasMore: page.hasMore }
        : { messages: merge(state.messages, page.messages) };
    });
  },

  async loadOlder() {
    const { messages, hasMore, loadingOlder } = get();
    const oldest = messages[0];
    if (!hasMore || loadingOlder || oldest === undefined) {
      return;
    }
    set({ loadingOlder: true });
    try {
      const page = await fetchHistory(oldest.position);
      set((state) => ({
        messages: merge(state.messages, page.messages),
        hasMore: page.hasMore,
      }));
    } finally {
      set({ loadingOlder: false });
    }
  },

  send(body) {
    const clientToken = crypto.randomUUID();
    set((state) => ({ pending: [...state.pending, { clientToken, body, errorCode: null }] }));
    void get().flushPending();
  },

  async flushPending() {
    if (flushing) {
      return;
    }
    flushing = true;
    try {
      // La file est relue à chaque tour : un message ajouté pendant un envoi part à la suite.
      for (;;) {
        const item = get().pending.find((entry) => entry.errorCode === null);
        if (item === undefined) {
          return;
        }
        try {
          const message = await sendMessage(item.clientToken, item.body);
          set((state) => ({
            messages: merge(state.messages, [message]),
            pending: state.pending.filter((entry) => entry.clientToken !== item.clientToken),
          }));
        } catch (error) {
          const code = error instanceof ApiError ? error.code : "internal_error";
          if (code === "network_error" || code === "service_unavailable") {
            // L'ordre des messages est préservé : les suivants attendent aussi.
            return;
          }
          set((state) => ({
            pending: state.pending.map((entry) =>
              entry.clientToken === item.clientToken ? { ...entry, errorCode: code } : entry,
            ),
          }));
        }
      }
    } finally {
      flushing = false;
    }
  },

  discardPending(clientToken) {
    set((state) => ({
      pending: state.pending.filter((entry) => entry.clientToken !== clientToken),
    }));
  },

  reset() {
    set({ messages: [], hasMore: false, loadingOlder: false, pending: [] });
  },
}));
