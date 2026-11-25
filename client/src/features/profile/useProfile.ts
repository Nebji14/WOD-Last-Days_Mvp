"use client";

/**
 * État de la fenêtre du profil.
 *
 * - Le compte et la liste des personnages se rechargent à chaque changement
 *   signalé par le serveur : création depuis une autre fenêtre, personnage
 *   joué ou supprimé.
 * - Le compte MJ n'a pas de personnage : la liste n'est pas demandée.
 * - Sans session, la fenêtre se ferme.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { type Account, fetchCurrentAccount } from "@/features/auth/api";
import { deleteCharacter, fetchCharacters, playCharacter } from "@/features/characters/api";
import type { Character } from "@/features/characters/model";
import { type PortraitFiles, removePortrait, setPortrait } from "@/features/characters/portrait";
import { ApiError } from "@/shared/api/client";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

import { removeAccountPortrait, setAccountPortrait } from "./accountApi";

const REALTIME_EVENTS = ["character.changed", "account.changed"] as const;

export interface ProfileState {
  readonly account: Account | null;
  readonly characters: readonly Character[];
  /** Code de la dernière erreur, à traduire par `errorLabel`. */
  readonly errorCode: string | null;
  /** Personnage, ou compte, dont une action est en cours. */
  readonly busyId: string | null;
  readonly play: (characterId: string) => void;
  readonly remove: (characterId: string) => void;
  /** Donne une image à une forme, à la place de la précédente. */
  readonly changePortrait: (characterId: string, sheetId: string, files: PortraitFiles) => void;
  readonly clearPortrait: (characterId: string, sheetId: string) => void;
  /** Donne une photo au compte du MJ, ou la retire. */
  readonly changeOwnPortrait: (accountId: string, files: PortraitFiles) => void;
  readonly clearOwnPortrait: (accountId: string) => void;
  /** Relit le compte et les personnages. */
  readonly refresh: () => void;
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

  const refresh = useCallback(() => void reload(), [reload]);
  useDetachedRealtime(REALTIME_EVENTS, refresh);

  /** Lance une action sur un personnage ou sur le compte, puis relit le profil. */
  const act = useCallback(
    (subjectId: string, action: () => Promise<unknown>) => {
      setBusyId(subjectId);
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

  const changePortrait = useCallback(
    (characterId: string, sheetId: string, files: PortraitFiles) =>
      act(characterId, () => setPortrait(sheetId, files)),
    [act],
  );
  const clearPortrait = useCallback(
    (characterId: string, sheetId: string) => act(characterId, () => removePortrait(sheetId)),
    [act],
  );
  const changeOwnPortrait = useCallback(
    (accountId: string, files: PortraitFiles) => act(accountId, () => setAccountPortrait(files)),
    [act],
  );
  const clearOwnPortrait = useCallback(
    (accountId: string) => act(accountId, removeAccountPortrait),
    [act],
  );

  return {
    account,
    characters,
    errorCode,
    busyId,
    play,
    remove,
    changePortrait,
    clearPortrait,
    changeOwnPortrait,
    clearOwnPortrait,
    refresh,
  };
}
