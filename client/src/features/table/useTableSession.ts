"use client";

/**
 * Session de la table de jeu : compte connecté, connexion temps réel, présence
 * et déconnexion.
 *
 * La table est réservée aux comptes connectés : sans session, ou dès que la
 * session est fermée (déconnexion depuis une autre fenêtre, expiration), le
 * navigateur revient à l'écran de connexion.
 */
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { type Account, fetchCurrentAccount, logout } from "@/features/auth/api";
import { loginPathAfterLogout, PLAYER_LOGIN_PATH } from "@/features/auth/routes";
import {
  createRealtimeClient,
  type RealtimeClient,
  type RealtimeStatus,
} from "@/shared/realtime/client";
import { fetchRealtimeTicket, realtimeUrl } from "@/shared/realtime/ticket";
import { setFlashForNextPage } from "@/shared/ui/flash";
import { closeAllDetached } from "@/shared/windows/detached";

import { parseTableState, type TableState } from "./state";

export interface TableSession {
  /** `null` tant que le compte n'est pas chargé. */
  readonly account: Account | null;
  /** Client temps réel, `null` tant que le compte n'est pas chargé. */
  readonly realtime: RealtimeClient | null;
  readonly status: RealtimeStatus;
  /** Dernier état de présence reçu, `null` avant le premier. */
  readonly table: TableState | null;
  readonly loggingOut: boolean;
  /** Ferme la session puis revient à l'écran de connexion (US-003, 03-I4). */
  logOut(): void;
}

export function useTableSession(): TableSession {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [status, setStatus] = useState<RealtimeStatus>("connecting");
  const [table, setTable] = useState<TableState | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const realtime = useMemo(
    () =>
      account === null
        ? null
        : createRealtimeClient({ url: realtimeUrl(), fetchTicket: fetchRealtimeTicket }),
    [account],
  );

  useEffect(() => {
    let cancelled = false;
    fetchCurrentAccount()
      .catch(() => null)
      .then((current) => {
        if (cancelled) {
          return;
        }
        if (current === null) {
          router.replace(PLAYER_LOGIN_PATH);
        } else {
          setAccount(current);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  useEffect(() => {
    if (account === null || realtime === null) {
      return;
    }
    const unsubscribeState = realtime.on("table.state", (data) => {
      const state = parseTableState(data);
      if (state !== null) {
        setTable(state);
      }
    });
    const unsubscribeStatus = realtime.onStatus((next) => {
      setStatus(next);
      if (next === "unauthenticated") {
        closeAllDetached();
        router.replace(loginPathAfterLogout(account.role));
      }
    });
    realtime.start();
    return () => {
      unsubscribeState();
      unsubscribeStatus();
      realtime.stop();
    };
  }, [account, realtime, router]);

  // T3 : fermer la fenêtre principale ferme aussi les fenêtres détachées.
  useEffect(() => {
    window.addEventListener("pagehide", closeAllDetached);
    return () => window.removeEventListener("pagehide", closeAllDetached);
  }, []);

  function logOut(): void {
    if (account === null || loggingOut) {
      return;
    }
    setLoggingOut(true);
    realtime?.stop();
    closeAllDetached();
    // La déconnexion locale a lieu même si le serveur est injoignable.
    void logout()
      .catch(() => undefined)
      .then(() => {
        setFlashForNextPage("loggedOut");
        router.replace(loginPathAfterLogout(account.role));
      });
  }

  return { account, realtime, status, table, loggingOut, logOut };
}
