"use client";

/**
 * Images de la table vues par tous (03-A2, 03-I5, 08a).
 *
 * La scène se relit à chaque (re)connexion, à chaque changement signalé par le
 * serveur (≤ 1 s, CDC 12.3) et régulièrement pour renouveler les liens signés.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import type { RealtimeClient } from "@/shared/realtime/client";

import { fetchScene, type TableScene } from "./api";

const LINK_REFRESH_MS = 30 * 60 * 1000;
const EMPTY_SCENE: TableScene = { shown: null, pile: [] };

export function useTableImages(realtime: RealtimeClient | null): TableScene {
  const [scene, setScene] = useState<TableScene>(EMPTY_SCENE);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const reload = useCallback(async () => {
    try {
      const next = await fetchScene();
      if (mountedRef.current) {
        setScene(next);
      }
    } catch (error) {
      // La scène précédente reste affichée ; la prochaine relecture la rattrape.
      console.warn("Images de la table indisponibles", error);
    }
  }, []);

  useEffect(() => {
    if (realtime === null) {
      return;
    }
    const unsubscribeEvent = realtime.on("images.changed", () => void reload());
    // Chaque (re)connexion rattrape ce qui a pu être manqué pendant la coupure.
    const unsubscribeStatus = realtime.onStatus((next) => {
      if (next === "online") {
        void reload();
      }
    });
    return () => {
      unsubscribeEvent();
      unsubscribeStatus();
    };
  }, [realtime, reload]);

  useEffect(() => {
    const timer = window.setInterval(() => void reload(), LINK_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [reload]);

  return scene;
}
