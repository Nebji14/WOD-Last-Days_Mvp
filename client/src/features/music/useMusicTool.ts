"use client";

/**
 * État de l'outil Musique du MJ : lecture, file et playlists, relues à chaque
 * changement signalé par le serveur. Sans session, la fenêtre se ferme.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

import { fetchDeck, fetchPlaylists } from "./api";
import type { Deck, HeardMusic, Playlist } from "./model";

const EVENTS = ["music.changed", "playlists.changed"] as const;

/** Lance une action, signale son éventuel échec, puis relit l'état. */
export type Act = (action: () => Promise<unknown>) => Promise<boolean>;

interface ToolState {
  readonly deck: Deck;
  readonly heard: HeardMusic;
  readonly playlists: readonly Playlist[];
}

export interface MusicTool {
  /** `null` tant que l'état n'est pas chargé. */
  readonly state: ToolState | null;
  readonly errorCode: string | null;
  readonly act: Act;
}

export function useMusicTool(): MusicTool {
  const [state, setState] = useState<ToolState | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const requestRef = useRef(0);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const fail = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.status === 401) {
      window.close();
    } else if (mountedRef.current) {
      setErrorCode(error instanceof ApiError ? error.code : "internal_error");
    }
  }, []);

  const reload = useCallback(async (): Promise<void> => {
    requestRef.current += 1;
    const request = requestRef.current;
    try {
      const [deck, playlists] = await Promise.all([fetchDeck(), fetchPlaylists()]);
      // Seule la dernière relecture compte : une réponse tardive ne revient pas en arrière.
      if (mountedRef.current && request === requestRef.current) {
        setState({ deck, heard: { now: deck.now, receivedAt: performance.now() }, playlists });
      }
    } catch (error) {
      fail(error);
    }
  }, [fail]);

  useDetachedRealtime(
    EVENTS,
    useCallback(() => void reload(), [reload]),
  );

  const act = useCallback<Act>(
    async (action) => {
      setErrorCode(null);
      try {
        await action();
        await reload();
        return true;
      } catch (error) {
        fail(error);
        return false;
      }
    },
    [fail, reload],
  );

  return { state, errorCode, act };
}
