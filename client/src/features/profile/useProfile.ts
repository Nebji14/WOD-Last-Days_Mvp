"use client";

/**
 * État de la fenêtre du profil (écran 09).
 *
 * - Le compte et la liste des personnages se rechargent à chaque changement
 *   signalé par le serveur : création depuis une autre fenêtre, personnage
 *   joué ou supprimé (09-I3, 09-I4).
 * - Le compte MJ n'a pas de personnage : la liste n'est pas demandée.
 * - Sans session, la fenêtre se ferme (T3).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { type Account, fetchCurrentAccount } from "@/features/auth/api";
import { deleteCharacter, fetchCharacters, playCharacter } from "@/features/characters/api";
import type { Character } from "@/features/characters/model";
import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

export interface ProfileState {
  readonly account: Account | null;
  readonly characters: readonly Character[];
  /** Code de la dernière erreur, à traduire par `errorLabel`. */
  readonly errorCode: string | null;
  /** Personnage dont une action est en cours. */
  readonly busyId: string | null;
  readonly play: (characterId: string) => void;
  readonly remove: (characterId: string) => void;
}

function errorCodeOf(error: unknown): string {
  return error instanceof ApiError ? error.code : "internal_error";
}

export function useProfile(): ProfileState {
  const [account, setAccount] = useState<Account | null>(null);
  const [characters, setCharacters] = useState<readonly Character[]>([]);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const reload = useCallback(async (): Promise<void> => {
    try {
      const current = await fetchCurrentAccount();
      if (current === null) {
        window.close();
        return;
      }
      const owned = current.role === "player" ? await fetchCharacters() : [];
      if (mountedRef.current) {
        setAccount(current);
        setCharacters(owned);
      }
    } catch (error) {
      if (mountedRef.current) {
        setErrorCode(errorCodeOf(error));
      }
    }
  }, []);

  useDetachedRealtime(
    "character.changed",
    useCallback(() => void reload(), [reload]),
  );

  /** Lance une action sur un personnage, puis relit la liste. */
  const act = useCallback(
    (characterId: string, action: () => Promise<unknown>) => {
      setBusyId(characterId);
      setErrorCode(null);
      void action()
        .then(reload)
        .catch((error: unknown) => {
          if (mountedRef.current) {
            setErrorCode(errorCodeOf(error));
          }
        })
        .finally(() => {
          if (mountedRef.current) {
            setBusyId(null);
          }
        });
    },
    [reload],
  );

  const play = useCallback(
    (characterId: string) => act(characterId, () => playCharacter(characterId)),
    [act],
  );
  const remove = useCallback(
    (characterId: string) => act(characterId, () => deleteCharacter(characterId)),
    [act],
  );

  return { account, characters, errorCode, busyId, play, remove };
}
