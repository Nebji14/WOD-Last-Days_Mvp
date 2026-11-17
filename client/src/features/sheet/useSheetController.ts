"use client";

/**
 * État et enregistrements d'une fenêtre de fiche (écrans 05).
 *
 * - La fiche se recharge dès que le serveur signale un changement : une
 *   modification faite par le MJ ou depuis une autre fenêtre apparaît en direct
 *   (US-009 · CA1, 05-E3).
 * - Chaque écriture renvoie la fiche à jour. Une saisie refusée laisse la fiche
 *   telle qu'elle est et affiche la règle en cause (05-E2).
 * - En cas de coupure, l'écriture est retentée seule jusqu'à réussir : rien
 *   n'est à ressaisir (05-E4, CDC 12.3).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { fetchCharacter } from "@/features/characters/api";
import type { Character } from "@/features/characters/model";
import { ApiError, isRecord } from "@/shared/api/client";
import { errorLabel, labels, ruleLabel } from "@/shared/i18n";
import { useDetachedRealtime } from "@/shared/realtime/useDetachedRealtime";

export type SheetStatus = "loading" | "ready" | "missing";

export interface SheetNotice {
  readonly kind: "refused" | "retrying";
  readonly text: string;
}

/** Lance une écriture qui renvoie le personnage à jour. Retourne `true` si elle a réussi. */
export type RunAction = (action: () => Promise<Character>) => Promise<boolean>;

export interface SheetController {
  readonly status: SheetStatus;
  readonly character: Character | null;
  readonly notice: SheetNotice | null;
  readonly run: RunAction;
  /** Remplace la fiche affichée par une version reçue du serveur. */
  readonly accept: (character: Character) => void;
  readonly dismissNotice: () => void;
}

const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000] as const;
const NOTICE_DURATION_MS = 5000;

function isUnreachable(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.code === "network_error" || error.code === "service_unavailable")
  );
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export function useSheetController(characterId: string): SheetController {
  const [status, setStatus] = useState<SheetStatus>("loading");
  const [character, setCharacter] = useState<Character | null>(null);
  const [notice, setNotice] = useState<SheetNotice | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const reload = useCallback(async (): Promise<void> => {
    try {
      const loaded = await fetchCharacter(characterId);
      if (mountedRef.current) {
        setCharacter(loaded);
        setStatus("ready");
      }
    } catch (error) {
      if (!mountedRef.current || !(error instanceof ApiError)) {
        return;
      }
      if (error.status === 401) {
        window.close();
      } else if (error.status === 403 || error.status === 404) {
        setStatus("missing");
      }
    }
  }, [characterId]);

  useDetachedRealtime(
    "character.changed",
    useCallback(
      (data: unknown) => {
        if (data === null || (isRecord(data) && data.character_id === characterId)) {
          void reload();
        }
      },
      [characterId, reload],
    ),
  );

  useEffect(() => {
    if (notice?.kind !== "refused") {
      return;
    }
    const timer = window.setTimeout(() => setNotice(null), NOTICE_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const run = useCallback<RunAction>(
    async (action) => {
      for (let attempt = 0; mountedRef.current; attempt += 1) {
        try {
          const updated = await action();
          if (mountedRef.current) {
            setCharacter(updated);
            setNotice((current) => (current?.kind === "retrying" ? null : current));
          }
          return true;
        } catch (error) {
          if (!mountedRef.current) {
            return false;
          }
          if (isUnreachable(error)) {
            setNotice({ kind: "retrying", text: labels.sheet.retrying });
            await wait(RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)] ?? 8000);
            continue;
          }
          setNotice({ kind: "refused", text: refusalText(error) });
          if (error instanceof ApiError && error.status === 404) {
            setStatus("missing");
          } else {
            void reload();
          }
          return false;
        }
      }
      return false;
    },
    [reload],
  );

  const accept = useCallback((next: Character) => setCharacter(next), []);
  const dismissNotice = useCallback(() => setNotice(null), []);

  return { status, character, notice, run, accept, dismissNotice };
}

/** Message expliquant pourquoi une écriture a été refusée. */
function refusalText(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return errorLabel("internal_error");
  }
  if (error.code === "edit_conflict") {
    return labels.sheet.conflict;
  }
  if (error.code === "rule_violation") {
    return ruleLabel(error.details[0]?.rule ?? "");
  }
  return errorLabel(error.code);
}
