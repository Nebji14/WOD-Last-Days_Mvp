"use client";

/**
 * Écran provisoire affiché après la connexion. Les tables 03 et 03-MJ le
 * remplacent à l'étape 3.
 *
 * Il assure déjà deux comportements définitifs : l'accès réservé aux comptes
 * connectés et la déconnexion avec retour à l'écran de connexion (US-003, 08c).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { type Account, fetchCurrentAccount, logout } from "@/features/auth/api";
import { loginPathAfterLogout, PLAYER_LOGIN_PATH } from "@/features/auth/routes";
import { labels } from "@/shared/i18n";
import { setFlashForNextPage } from "@/shared/ui/flash";

export function TablePlaceholder() {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCurrentAccount()
      .then((current) => {
        if (cancelled) {
          return;
        }
        if (current === null) {
          router.replace(PLAYER_LOGIN_PATH);
        } else {
          setAccount(current);
        }
      })
      .catch(() => {
        if (!cancelled) {
          router.replace(PLAYER_LOGIN_PATH);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleLogout(role: Account["role"]): Promise<void> {
    setBusy(true);
    // La déconnexion locale a lieu même si le serveur est injoignable.
    await logout().catch(() => undefined);
    setFlashForNextPage("loggedOut");
    router.replace(loginPathAfterLogout(role));
  }

  if (account === null) {
    return (
      <main className="bg-night text-ink-muted flex min-h-screen items-center justify-center text-xl italic">
        {labels.table.loading}
      </main>
    );
  }

  return (
    <main className="bg-night flex min-h-screen flex-col items-center justify-center gap-5">
      <p className="text-ink-muted text-xl italic">{labels.table.placeholder}</p>
      <p className="text-ink text-2xl font-semibold">
        {labels.table.connectedAs} {account.displayName} ·{" "}
        <span className={account.role === "gm" ? "text-gm" : "text-gold"}>
          {account.role === "gm" ? labels.table.roleGm : labels.table.rolePlayer}
        </span>
      </p>
      <button
        type="button"
        disabled={busy}
        onClick={() => void handleLogout(account.role)}
        className="border-line-strong font-display text-ink hover:border-gold cursor-pointer rounded-xs border px-5 py-2.5 text-[11px] font-bold tracking-[3px] disabled:opacity-60"
      >
        {labels.table.logout}
      </button>
    </main>
  );
}
