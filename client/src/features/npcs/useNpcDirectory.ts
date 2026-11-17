"use client";

/**
 * État de l'outil PNJ du MJ.
 *
 * La liste se relit à chaque changement signalé par le serveur : PNJ créé,
 * modifié depuis sa fiche ou supprimé, catégorie changée. Sans session, la
 * fenêtre se ferme.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

import { fetchDirectory, type NpcDirectory } from "./api";

const REALTIME_EVENTS = ["npcs.changed", "character.changed"] as const;

export interface NpcDirectoryState {
  readonly directory: NpcDirectory | null;
  readonly errorCode: string | null;
  /** Lance une action, signale son éventuel échec, puis relit la liste. */
  readonly act: (action: () => Promise<unknown>) => Promise<boolean>;
}

export function useNpcDirectory(): NpcDirectoryState {
  const [directory, setDirectory] = useState<NpcDirectory | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const mountedRef = useRef(true);

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
    try {
      const next = await fetchDirectory();
      if (mountedRef.current) {
        setDirectory(next);
      }
    } catch (error) {
      fail(error);
    }
  }, [fail]);

  useDetachedRealtime(
    REALTIME_EVENTS,
    useCallback(() => void reload(), [reload]),
  );

  const act = useCallback(
    async (action: () => Promise<unknown>): Promise<boolean> => {
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

  return { directory, errorCode, act };
}
