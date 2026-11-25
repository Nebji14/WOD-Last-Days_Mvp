"use client";

/**
 * Fenêtre de l'outil Musique du MJ : lecture en cours, recherche, file et
 * playlists. Le son sort de la table, pas de cette fenêtre. Le serveur refuse
 * l'outil à tout autre compte.
 */
import { useEffect, useState } from "react";

import { errorLabel, fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";

import { deletePlaylist } from "../api";
import { useMusicTool } from "../useMusicTool";
import { DeckPanel } from "./DeckPanel";
import { PlaylistsPanel } from "./PlaylistsPanel";
import { QueuePanel } from "./QueuePanel";
import { SearchPanel } from "./SearchPanel";

const MESSAGE = "text-ink-muted flex flex-1 items-center justify-center p-8 text-xl italic";

interface Pending {
  readonly title: string;
  readonly question: string;
  readonly run: () => void;
}

export function MusicToolScreen() {
  const { state, errorCode, act } = useMusicTool();
  const text = labels.musicTool;
  const [pending, setPending] = useState<Pending | null>(null);

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  return (
    <div className="bg-night text-ink flex min-h-screen flex-col lg:h-screen">
      <DetachedTitleBar title={text.windowTitle} subtitle={text.subtitle} closeLabel={text.close} />
      {errorCode !== null && (
        <p
          role="alert"
          className="border-blood-line bg-danger-panel text-danger-bright shrink-0 border-b px-4 py-2 text-[15px] sm:px-8"
        >
          {errorLabel(errorCode)}
        </p>
      )}
      {state === null ? (
        <main className={MESSAGE}>{text.loading}</main>
      ) : (
        <main className="flex min-h-0 flex-1 flex-col gap-4 p-4 sm:p-6">
          <DeckPanel deck={state.deck} heard={state.heard} act={act} />
          <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)]">
            <SearchPanel playlists={state.playlists} act={act} />
            <QueuePanel
              queue={state.deck.queue}
              act={act}
              onClear={(run) =>
                setPending({ title: text.clearTitle, question: text.clearQuestion, run })
              }
            />
            <PlaylistsPanel
              playlists={state.playlists}
              act={act}
              onDelete={(playlist) =>
                setPending({
                  title: text.deleteTitle,
                  question: fill(text.deleteQuestion, { name: playlist.name }),
                  run: () => void act(() => deletePlaylist(playlist.id)),
                })
              }
              onRemoveTrack={(entry, run) =>
                setPending({
                  title: text.removeTitle,
                  question: fill(text.removeQuestion, { name: entry.track.title }),
                  run,
                })
              }
            />
          </div>
        </main>
      )}
      <ConfirmDialog
        open={pending !== null}
        title={pending?.title ?? ""}
        question={pending?.question ?? ""}
        confirmLabel={text.delete}
        cancelLabel={text.cancel}
        onConfirm={() => {
          pending?.run();
          setPending(null);
        }}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}
