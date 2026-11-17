"use client";

/**
 * Fenêtre détachée de la fiche de personnage (écrans 05a, 05b, 05c).
 *
 * Ouverte par le joueur propriétaire (US-008, US-009) ou par le MJ (US-026,
 * US-027) ; le serveur refuse toute autre lecture. Barre de titre, onglets des
 * formes (F1), puis la face choisie : RECTO, VERSO ou NOTES, avec un court
 * fondu au changement (Q05-1).
 */
import { useEffect, useState } from "react";

import { mainSheet } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { useSheetController } from "../useSheetController";
import { FormTabs } from "./FormTabs";
import { NotesFace } from "./NotesFace";
import { SheetProvider } from "./primitives";
import { RectoFace, VersoFace } from "./SheetFaces";
import { type SheetFace, SheetTitleBar } from "./SheetTitleBar";

const MESSAGE =
  "bg-night text-ink-muted flex min-h-screen items-center justify-center p-8 text-xl italic";

export function SheetScreen({ characterId }: { readonly characterId: string }) {
  const { status, character, notice, run, dismissNotice } = useSheetController(characterId);
  const [face, setFace] = useState<SheetFace>("recto");
  const [editing, setEditing] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  const main = character === null ? null : mainSheet(character);
  const sheet = character?.sheets.find((candidate) => candidate.id === activeId) ?? main;
  const title = main?.texts.name ?? "";

  useEffect(() => {
    document.title = title === "" ? labels.sheet.windowTitle : title;
  }, [title]);

  if (status === "missing") {
    return <main className={MESSAGE}>{labels.sheet.missing}</main>;
  }
  if (character === null || sheet === null) {
    return <main className={MESSAGE}>{labels.sheet.loading}</main>;
  }

  return (
    <SheetProvider value={{ character, sheet, editing, run }}>
      <div className="bg-night text-ink flex h-screen flex-col">
        <SheetTitleBar
          name={title}
          owner={character.owner_name}
          face={face}
          onFace={setFace}
          editing={editing}
          onEditing={setEditing}
        />
        <FormTabs
          character={character}
          activeId={sheet.id}
          onSelect={setActiveId}
          editing={editing}
          run={run}
        />
        {notice !== null && (
          <div
            role={notice.kind === "refused" ? "alert" : "status"}
            className={`flex shrink-0 items-center justify-between gap-4 border-b px-8 py-2 text-[15px] ${
              notice.kind === "refused"
                ? "border-blood-line bg-danger-panel text-danger-bright"
                : "border-copper bg-copper-deep/20 text-copper-light"
            }`}
          >
            <span>{notice.text}</span>
            {notice.kind === "refused" && (
              <button
                type="button"
                aria-label={labels.sheet.close}
                onClick={dismissNotice}
                className="cursor-pointer px-1"
              >
                ✕
              </button>
            )}
          </div>
        )}
        <main
          key={face}
          className={`animate-face-in min-h-0 flex-1 px-8 py-4 ${
            face === "notes" ? "overflow-hidden" : "overflow-y-auto"
          }`}
        >
          {face === "recto" && <RectoFace />}
          {face === "verso" && <VersoFace />}
          {face === "notes" && <NotesFace />}
        </main>
      </div>
    </SheetProvider>
  );
}
