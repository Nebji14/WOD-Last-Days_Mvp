"use client";

/**
 * Fenêtre du profil, ouverte par l'icône de profil de la table.
 *
 * Joueur : son compte et ses personnages. MJ : son compte seulement, puisqu'il
 * n'a pas de personnage.
 */
import { useEffect } from "react";

import type { Account } from "@/features/auth/api";
import { mainSheet } from "@/features/characters/model";
import { errorLabel, labels } from "@/shared/i18n";
import { DetachedTitleBar } from "@/shared/ui/DetachedTitleBar";

import type { GoogleResult } from "../googleResult";
import { type ProfileState, useProfile } from "../useProfile";
import { AccountPanel } from "./AccountPanel";
import { CharactersPanel } from "./CharactersPanel";
import type { ProfilePictureSource } from "./ProfilePicture";

const MESSAGE =
  "bg-night text-ink-muted flex min-h-screen items-center justify-center p-8 text-xl italic";

/** Photo du profil : celle du compte pour le MJ, celle du personnage joué pour un joueur. */
function pictureOf(profile: ProfileState, account: Account): ProfilePictureSource | null {
  if (account.role === "gm") {
    return {
      portrait: account.portrait,
      name: labels.table.gm.initials,
      busy: profile.busyId === account.id,
      onSave: (files) => profile.changeOwnPortrait(account.id, files),
      onRemove: () => profile.clearOwnPortrait(account.id),
    };
  }
  const played = profile.characters.find((character) => character.is_played);
  if (played === undefined) {
    return null;
  }
  const sheet = mainSheet(played);
  return {
    portrait: sheet.portrait,
    name: sheet.texts.name || account.displayName,
    busy: profile.busyId === played.id,
    onSave: (files) => profile.changePortrait(played.id, sheet.id, files),
    onRemove: () => profile.clearPortrait(played.id, sheet.id),
  };
}

interface ProfileScreenProps {
  /** Résultat à afficher au retour de Google, `null` sinon. */
  readonly googleResult: GoogleResult | null;
}

export function ProfileScreen({ googleResult }: ProfileScreenProps) {
  const profile = useProfile();
  const { account, characters, errorCode, busyId, changePortrait, clearPortrait } = profile;
  const text = labels.profile;

  useEffect(() => {
    document.title = text.windowTitle;
  }, [text.windowTitle]);

  // Le résultat de Google n'est annoncé qu'une fois : recharger ne le répète pas.
  useEffect(() => {
    if (googleResult !== null) {
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, [googleResult]);

  if (account === null) {
    return (
      <main className={MESSAGE}>{errorCode === null ? text.loading : errorLabel(errorCode)}</main>
    );
  }
  const isGm = account.role === "gm";

  return (
    <div className="bg-night text-ink flex min-h-dvh flex-col lg:h-screen">
      <DetachedTitleBar
        title={text.windowTitle}
        subtitle={isGm ? text.subtitleGm : text.subtitle}
        closeLabel={text.close}
      />
      <main
        className={`grid min-h-0 flex-1 content-start gap-4 p-4 sm:p-8 lg:content-stretch ${
          isGm
            ? "grid-cols-1 lg:grid-cols-[360px] lg:justify-center"
            : "grid-cols-1 lg:grid-cols-[360px_minmax(0,1fr)]"
        }`}
      >
        <AccountPanel
          account={account}
          picture={pictureOf(profile, account)}
          // Un joueur voit l'erreur à côté de ses personnages.
          errorCode={isGm ? errorCode : null}
          googleResult={googleResult}
          onChanged={profile.refresh}
        />
        {!isGm && (
          <CharactersPanel
            characters={characters}
            busyId={busyId}
            errorCode={errorCode}
            onPlay={profile.play}
            onDelete={profile.remove}
            onPortrait={changePortrait}
            onRemovePortrait={clearPortrait}
          />
        )}
      </main>
    </div>
  );
}
