"use client";

/**
 * Synchronisation du chat avec le serveur.
 *
 * - Chaque événement `chat.message` met à jour le message concerné : création,
 *   modification ou suppression.
 * - Un participant qui change de nom affiché est renommé sur ses messages.
 * - À chaque (re)connexion, les messages récents sont rechargés pour rattraper
 *   ce qui a été manqué, puis les envois en attente repartent.
 */
import { useEffect } from "react";

import type { RealtimeClient, RealtimeStatus } from "@/shared/realtime/client";

import { parseMessage, parseRenamedAccount } from "./api";
import { useChatStore } from "./store";

const PENDING_RETRY_MS = 5000;

export function useChatSync(realtime: RealtimeClient | null, status: RealtimeStatus): void {
  useEffect(() => {
    if (realtime === null) {
      return;
    }
    const unsubscribe = realtime.on("chat.message", (data) => {
      const message = parseMessage(data);
      if (message !== null) {
        useChatStore.getState().upsert(message);
      }
    });
    const unsubscribeRename = realtime.on("account.changed", (data) => {
      const renamed = parseRenamedAccount(data);
      if (renamed !== null) {
        useChatStore.getState().renameAuthor(renamed.id, renamed.displayName);
      }
    });
    return () => {
      unsubscribe();
      unsubscribeRename();
      useChatStore.getState().reset();
    };
  }, [realtime]);

  useEffect(() => {
    if (status !== "online") {
      return;
    }
    const chat = useChatStore.getState();
    // Un échec est rattrapé à la prochaine reconnexion ; les messages suivants arrivent par le temps réel.
    void chat.loadLatest().catch(() => undefined);
    void chat.flushPending();
  }, [status]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const chat = useChatStore.getState();
      if (chat.pending.some((entry) => entry.errorCode === null)) {
        void chat.flushPending();
      }
    }, PENDING_RETRY_MS);
    return () => window.clearInterval(timer);
  }, []);
}
