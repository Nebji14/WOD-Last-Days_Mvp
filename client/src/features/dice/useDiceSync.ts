"use client";

/** Reçoit les vagues de dés de la table et les met en file d'affichage. */
import { useEffect } from "react";

import type { RealtimeClient } from "@/shared/realtime/client";

import { parseRoll } from "./model";
import { useDiceStore } from "./store";

export function useDiceSync(realtime: RealtimeClient | null): void {
  useEffect(() => {
    if (realtime === null) {
      return;
    }
    const unsubscribe = realtime.on("dice.roll", (data) => {
      const roll = parseRoll(data);
      if (roll !== null) {
        useDiceStore.getState().receive(roll);
      }
    });
    return () => {
      unsubscribe();
      useDiceStore.getState().reset();
    };
  }, [realtime]);
}
