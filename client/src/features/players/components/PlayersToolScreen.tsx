"use client";

/**
 * Fenêtre de l'outil Joueurs du MJ : liste à gauche, détail du joueur choisi à
 * droite. Le serveur refuse la liste à tout autre compte que le MJ.
 */
import { useEffect } from "react";

import { errorLabel, labels } from "@/shared/i18n";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";

import { usePlayersTool } from "../usePlayersTool";
import { PlayerDetail } from "./PlayerDetail";
import { PlayerList } from "./PlayerList";

const MESSAGE = "text-ink-muted flex flex-1 items-center justify-center p-8 text-xl italic";

export function PlayersToolScreen() {
  const tool = usePlayersTool();
  const { players, selectedId, characters, errorCode, busyId, select, awaken } = tool;
  const text = labels.playersTool;
  const selected = players?.find((player) => player.id === selectedId) ?? null;

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  return (
    <div className="bg-night text-ink flex h-screen flex-col">
      <DetachedTitleBar title={text.windowTitle} subtitle={text.subtitle} closeLabel={text.close} />
      {errorCode !== null && (
        <p
          role="alert"
          className="border-blood-line bg-danger-panel text-danger-bright shrink-0 border-b px-8 py-2 text-[15px]"
        >
          {errorLabel(errorCode)}
        </p>
      )}
      {players === null ? (
        <main className={MESSAGE}>{text.loading}</main>
      ) : (
        <main className="grid min-h-0 flex-1 grid-cols-[420px_minmax(0,1fr)] gap-6 p-8">
          <PlayerList players={players} selectedId={selectedId} onSelect={select} />
          {selected === null ? (
            <p className={MESSAGE}>{text.selectHint}</p>
          ) : (
            <PlayerDetail
              player={selected}
              characters={characters}
              busyId={busyId}
              onAwaken={awaken}
              onReactivate={() => tool.reactivate(selected.id)}
            />
          )}
        </main>
      )}
    </div>
  );
}
