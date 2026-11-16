/**
 * [En-tête] de la table (écrans 03 et 03-MJ).
 *
 * Vue joueur : [Statut de la partie] au centre. Vue MJ : le statut passe à
 * gauche et les [Outils MJ (icônes)] prennent le centre (03-MJ-D1).
 */
import type { Account } from "@/features/auth/api";
import { labels } from "@/shared/i18n";

import { initials } from "../seatLayout";
import { GmTools } from "./GmTools";

interface TableHeaderProps {
  readonly account: Account;
  readonly loggingOut: boolean;
  readonly onLogout: () => void;
}

/** Q03-2 : démarrer et arrêter la partie sont hors MVP, le statut est donc fixe (03-E1). */
function GameStatus({ className }: { readonly className: string }) {
  return (
    <p
      className={`border-line bg-panel font-display text-ink absolute top-[17px] flex h-[30px] items-center gap-2 rounded-full border pr-4 pl-3.5 text-[11px] font-bold tracking-[2px] ${className}`}
    >
      <span aria-hidden="true" className="bg-ink-faint size-2 rounded-full" />
      {labels.table.status}
    </p>
  );
}

export function TableHeader({ account, loggingOut, onLogout }: TableHeaderProps) {
  const isGm = account.role === "gm";

  return (
    <header className="border-line-soft absolute inset-x-0 top-0 z-20 h-16 border-b bg-[rgb(11_8_7/0.95)]">
      <p className="font-display text-ink-bright absolute top-3.5 left-8 text-[26px] leading-[35px] font-black tracking-[5px] [text-shadow:0_0_12px_rgb(255_90_20/0.6)]">
        {labels.app.game}
      </p>
      <p className="font-display text-gold absolute top-6 left-[196px] text-xs leading-4 font-bold tracking-[5px]">
        {labels.app.campaign}
      </p>

      <GameStatus className={isGm ? "left-[340px]" : "left-1/2 -translate-x-1/2"} />
      {isGm && <GmTools />}

      <button
        type="button"
        onClick={onLogout}
        disabled={loggingOut}
        className="border-line bg-panel font-display text-ink hover:border-gold absolute top-[15px] right-[77px] h-[34px] cursor-pointer rounded-xs border px-4 text-[11px] font-bold tracking-[2px] transition-colors disabled:cursor-wait disabled:opacity-60"
      >
        {labels.table.logout}
      </button>
      {/* TODO(US-012 · CA1, écran 09) : ouvrir le profil dans une fenêtre détachable (03-I3). */}
      <span
        role="img"
        aria-label={`${labels.table.profile} : ${account.displayName}`}
        title={account.displayName}
        className={`bg-field font-display absolute top-[13px] right-[26px] flex size-[38px] items-center justify-center rounded-full border-[1.5px] font-bold ${
          isGm ? "border-copper text-[12px] text-[#ca8f68]" : "border-gold text-gold text-[15px]"
        }`}
      >
        {isGm ? labels.table.gm.initials : initials(account.displayName).slice(0, 1)}
      </span>
    </header>
  );
}
