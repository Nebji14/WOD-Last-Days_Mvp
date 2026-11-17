"use client";

/**
 * Table de jeu, côté joueur et côté MJ.
 *
 * Les deux vues partagent la table, les sièges, le chat et les images du MJ. Le
 * MJ n'a pas de siège à lui et dispose de ses outils dans l'en-tête. La table et
 * le chat restent accessibles même sans partie en cours. Les jets de dés se
 * jouent par-dessus toute la fenêtre.
 */
import { ChatPanel } from "@/features/chat/components/ChatPanel";
import { useChatSync } from "@/features/chat/useChatSync";
import { DiceOverlay } from "@/features/dice/components/DiceOverlay";
import { GmDice } from "@/features/dice/components/GmDice";
import { useDiceSync } from "@/features/dice/useDiceSync";
import { TableImages } from "@/features/images/components/TableImages";
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
  useDiceSync(session.realtime);
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
    <>
      <ScaledStage>
        <main className="relative size-full overflow-hidden">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,#241911_0%,#100c09_55%,#050303_100%)]"
          />
          <EmberParticles className="top-16 opacity-70" density="sparse" />
          <TableHeader
            account={account}
            loggingOut={session.loggingOut}
            onLogout={session.logOut}
          />
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
          <TableImages
            realtime={session.realtime}
            isGm={isGm}
            gmName={table?.gm.displayName ?? labels.table.gm.unknownName}
          />
          {isGm && <GmDice />}
          <ConnectionNotice status={session.status} />
        </main>
      </ScaledStage>
      <DiceOverlay viewerId={account.id} />
    </>
  );
}
