"use client";

/**
 * Connexion temps réel d'une fenêtre détachée (fiche, création, profil, outils).
 *
 * Chaque fenêtre ouvre sa propre connexion pour rester synchronisée avec la
 * table. Quand la session se ferme (déconnexion depuis la fenêtre principale),
 * la fenêtre se ferme d'elle-même.
 */
import { useEffect, useRef, useState } from "react";

import { createRealtimeClient, type RealtimeStatus } from "./client";
import { fetchRealtimeTicket, realtimeUrl } from "./ticket";

/**
 * @param eventTypes type, ou liste de types, d'événements à écouter sur une
 *   seule connexion.
 * @param onEvent appelé à chaque événement écouté, et à chaque (re)connexion
 *   avec `null` pour rattraper ce qui a pu être manqué.
 * @returns l'état de la connexion.
 */
export function useDetachedRealtime(
  eventTypes: string | readonly string[],
  onEvent: (data: unknown) => void,
): RealtimeStatus {
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const handlerRef = useRef(onEvent);

  useEffect(() => {
    handlerRef.current = onEvent;
  }, [onEvent]);

  // Clé stable : une nouvelle liste aux mêmes types ne rouvre pas la connexion.
  const typesKey = typeof eventTypes === "string" ? eventTypes : eventTypes.join(",");

  useEffect(() => {
    const client = createRealtimeClient({ url: realtimeUrl(), fetchTicket: fetchRealtimeTicket });
    const unsubscribeEvents = typesKey
      .split(",")
      .map((type) => client.on(type, (data) => handlerRef.current(data)));
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
      unsubscribeEvents.forEach((unsubscribe) => unsubscribe());
      unsubscribeStatus();
      client.stop();
    };
  }, [typesKey]);

  return status;
}
