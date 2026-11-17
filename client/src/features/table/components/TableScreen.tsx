"use client";

/**
 * Table de jeu : écran 03 (joueur, US-012) et écran 03-MJ (MJ, US-028).
 *
 * Les deux vues partagent la table, les sièges et le chat. La vue MJ n'a pas
 * de « mon siège » et porte les outils du MJ dans l'en-tête (03-MJ-D1 à D5).
 * La table et le chat restent accessibles sans partie en cours (RM-018, 03-E1).
 */
import { ChatPanel } from "@/features/chat/components/ChatPanel";
import { useChatSync } from "@/features/chat/useChatSync";
import { labels } from "@/shared/i18n";
import { EmberParticles } from "@/shared/ui/EmberParticles";
import { ScaledStage } from "@/shared/ui/ScaledStage";

import { arrangeSeats } from "../seatLayout";
import { useTableSession } from "../useTableSession";
import { ConnectionNotice } from "./ConnectionNotice";
import { GmSeat } from "./GmSeat";
import { PlayerSeat } from "./PlayerSeat";
import { TableHeader } from "./TableHeader";
import { TableSurface } from "./TableSurface";

export function TableScreen() {
  const session = useTableSession();
  useChatSync(session.realtime, session.status);
  const { account, table } = session;

  if (account === null) {
    return (
      <main className="bg-night text-ink-muted flex min-h-screen items-center justify-center text-xl italic">
        {labels.table.loading}
      </main>
    );
  }

  const isGm = account.role === "gm";
  const seats = table?.seats ?? [];

  return (
    <ScaledStage>
      <main className="relative size-full overflow-hidden">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,#241911_0%,#100c09_55%,#050303_100%)]"
        />
        <EmberParticles className="top-16 opacity-70" density="sparse" />
        <TableHeader account={account} loggingOut={session.loggingOut} onLogout={session.logOut} />
        <TableSurface />
        {table !== null && (
          <GmSeat
            gm={table.gm}
            onlinePlayers={seats.filter((seat) => seat.online).length}
            isViewer={isGm}
          />
        )}
        {arrangeSeats(seats, isGm ? null : account.id).map((placed) => (
          <PlayerSeat key={placed.seat.accountId} {...placed} />
        ))}
        <ChatPanel viewerId={account.id} viewerIsGm={isGm} />
        <ConnectionNotice status={session.status} />
      </main>
    </ScaledStage>
  );
}
