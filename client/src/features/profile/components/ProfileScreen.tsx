"use client";

/**
 * Fenêtre du profil, ouverte par l'icône de profil de la table.
 *
 * Joueur : son compte et ses personnages. MJ : son compte seulement, puisqu'il
 * n'a pas de personnage.
 */
import { useEffect } from "react";

import { errorLabel, labels } from "@/shared/i18n";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";

import { useProfile } from "../useProfile";
import { AccountPanel } from "./AccountPanel";
import { CharactersPanel } from "./CharactersPanel";

const MESSAGE =
  "bg-night text-ink-muted flex min-h-screen items-center justify-center p-8 text-xl italic";

export function ProfileScreen() {
  const { account, characters, errorCode, busyId, play, remove } = useProfile();
  const text = labels.profile;

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  if (account === null) {
    return (
      <main className={MESSAGE}>{errorCode === null ? text.loading : errorLabel(errorCode)}</main>
    );
  }
  const isGm = account.role === "gm";

  return (
    <div className="bg-night text-ink flex h-screen flex-col">
      <DetachedTitleBar
        title={text.windowTitle}
        subtitle={isGm ? text.subtitleGm : text.subtitle}
        closeLabel={text.close}
      />
      <main
        className={`grid min-h-0 flex-1 gap-4 p-8 ${
          isGm ? "grid-cols-[360px] justify-center" : "grid-cols-[360px_minmax(0,1fr)]"
        }`}
      >
        <AccountPanel account={account} />
        {!isGm && (
          <CharactersPanel
            characters={characters}
            busyId={busyId}
            errorCode={errorCode}
            onPlay={play}
            onDelete={remove}
          />
        )}
      </main>
    </div>
  );
}
