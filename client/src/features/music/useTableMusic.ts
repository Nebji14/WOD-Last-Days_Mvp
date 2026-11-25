"use client";

/**
 * Lecture commune vue de la table. Elle est reçue en direct et relue à chaque
 * (re)connexion, pour reprendre au bon endroit.
 */
import { useEffect, useState } from "react";

import type { RealtimeClient } from "@/shared/realtime/client";

import { fetchNowPlaying } from "./api";
import { type HeardMusic, type NowPlaying, parseNowPlaying } from "./model";

export function useTableMusic(realtime: RealtimeClient | null): HeardMusic | null {
  const [heard, setHeard] = useState<HeardMusic | null>(null);

  useEffect(() => {
    if (realtime === null) {
      return;
    }
    let cancelled = false;
    // Une relecture partie avant un événement plus récent est ignorée.
    let version = 0;
    const receive = (now: NowPlaying): void => {
      version += 1;
      setHeard({ now, receivedAt: performance.now() });
    };
    const reload = async (): Promise<void> => {
      const startedAt = version;
      try {
        const now = await fetchNowPlaying();
        if (!cancelled && startedAt === version) {
          receive(now);
        }
      } catch (error) {
        // La musique déjà entendue continue ; le prochain événement la rattrape.
        console.warn("Musique de la table indisponible", error);
      }
    };
    const unsubscribeEvent = realtime.on("music.changed", (data) => {
      const now = parseNowPlaying(data);
      if (now !== null) {
        receive(now);
      }
    });
    const unsubscribeStatus = realtime.onStatus((next) => {
      if (next === "online") {
        void reload();
      }
    });
    return () => {
      cancelled = true;
      unsubscribeEvent();
      unsubscribeStatus();
    };
  }, [realtime]);

  return heard;
}
