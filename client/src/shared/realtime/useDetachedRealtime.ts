"use client";

/**
 * Connexion temps réel d'une fenêtre détachée (fiche, création, profil).
 *
 * Chaque fenêtre ouvre sa propre connexion pour rester synchronisée avec la
 * table et les autres fenêtres (règle T3). Quand la session se ferme
 * (déconnexion depuis la fenêtre principale), la fenêtre se ferme d'elle-même.
 */
import { useEffect, useRef, useState } from "react";

import { createRealtimeClient, type RealtimeStatus } from "./client";
import { fetchRealtimeTicket, realtimeUrl } from "./ticket";

/**
 * @param eventType type d'événement à écouter.
 * @param onEvent appelé à chaque événement de ce type, et à chaque (re)connexion
 *   avec `null` pour rattraper ce qui a pu être manqué.
 * @returns l'état de la connexion.
 */
export function useDetachedRealtime(
  eventType: string,
  onEvent: (data: unknown) => void,
): RealtimeStatus {
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const handlerRef = useRef(onEvent);

  useEffect(() => {
    handlerRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const client = createRealtimeClient({ url: realtimeUrl(), fetchTicket: fetchRealtimeTicket });
    const unsubscribeEvent = client.on(eventType, (data) => handlerRef.current(data));
    const unsubscribeStatus = client.onStatus((next) => {
      setStatus(next);
      if (next === "online") {
        handlerRef.current(null);
      }
      if (next === "unauthenticated") {
        window.close();
      }
    });
    client.start();
    return () => {
      unsubscribeEvent();
      unsubscribeStatus();
      client.stop();
    };
  }, [eventType]);

  return status;
}
