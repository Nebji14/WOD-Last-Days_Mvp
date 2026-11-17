"use client";

/**
 * État de l'outil Joueurs du MJ.
 *
 * - La liste et les personnages du joueur sélectionné se rechargent à chaque
 *   arrivée ou départ autour de la table et à chaque changement de personnage.
 * - Le premier joueur de la liste est sélectionné à l'ouverture.
 * - Sans session, la fenêtre se ferme.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { awakenCharacter, fetchCharacters } from "@/features/characters/api";
import type { Character } from "@/features/characters/model";
import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

import { fetchPlayers, type Player } from "./api";

const REALTIME_EVENTS = ["table.state", "character.changed"] as const;

export interface PlayersToolState {
  /** `null` tant que la liste n'est pas chargée. */
  readonly players: readonly Player[] | null;
  readonly selectedId: string | null;
  /** Personnages du joueur sélectionné. */
  readonly characters: readonly Character[];
  readonly errorCode: string | null;
  /** Personnage dont l'éveil est en cours d'enregistrement. */
  readonly busyId: string | null;
  readonly select: (playerId: string) => void;
  readonly awaken: (characterId: string) => void;
}

export function usePlayersTool(): PlayersToolState {
  const [players, setPlayers] = useState<readonly Player[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [characters, setCharacters] = useState<readonly Character[]>([]);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const selectedRef = useRef<string | null>(null);
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
      return;
    }
    if (mountedRef.current) {
      setErrorCode(error instanceof ApiError ? error.code : "internal_error");
    }
  }, []);

  /** Charge les personnages d'un joueur, si la sélection n'a pas changé entre-temps. */
  const loadCharacters = useCallback(async (ownerId: string): Promise<void> => {
    const owned = await fetchCharacters(ownerId);
    if (mountedRef.current && selectedRef.current === ownerId) {
      setCharacters(owned);
    }
  }, []);

  const reload = useCallback(async (): Promise<void> => {
    try {
      const list = await fetchPlayers();
      if (!mountedRef.current) {
        return;
      }
      const current = list.find((p) => p.id === selectedRef.current) ?? list[0] ?? null;
      selectedRef.current = current?.id ?? null;
      setPlayers(list);
      setSelectedId(selectedRef.current);
      if (current === null) {
        setCharacters([]);
      } else {
        await loadCharacters(current.id);
      }
    } catch (error) {
      fail(error);
    }
  }, [fail, loadCharacters]);

  useDetachedRealtime(
    REALTIME_EVENTS,
    useCallback(() => void reload(), [reload]),
  );

  const select = useCallback(
    (playerId: string) => {
      selectedRef.current = playerId;
      setSelectedId(playerId);
      setCharacters([]);
      loadCharacters(playerId).catch(fail);
    },
    [fail, loadCharacters],
  );

  const awaken = useCallback(
    (characterId: string) => {
      setBusyId(characterId);
      setErrorCode(null);
      awakenCharacter(characterId)
        .then(() => reload())
        .catch(fail)
        .finally(() => {
          if (mountedRef.current) {
            setBusyId(null);
          }
        });
    },
    [fail, reload],
  );

  return { players, selectedId, characters, errorCode, busyId, select, awaken };
}
