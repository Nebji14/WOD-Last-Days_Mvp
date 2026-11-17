"use client";

/**
 * Fenêtre de la fiche d'un personnage ou d'un PNJ.
 *
 * Ouverte par le propriétaire ou par le MJ ; le serveur refuse toute autre
 * lecture. Barre de titre, onglets des formes, puis la face choisie (RECTO,
 * VERSO ou NOTES) avec un court fondu au changement.
 */
import { useEffect, useState } from "react";

import { mainSheet } from "@/features/characters/model";
import { RollDock } from "@/features/dice/components/RollDock";
import { EMPTY_CHOICE, type RollChoice } from "@/features/dice/pool";
import { RollModeProvider } from "@/features/dice/rollMode";
import { categoryLabel } from "@/features/npcs/categories";
import { labels } from "@/shared/i18n";

import { useNpcCategories } from "../useNpcCategories";
import { useSheetController } from "../useSheetController";
import { FormTabs } from "./FormTabs";
import { NotesFace } from "./NotesFace";
import { SheetProvider } from "./primitives";
import { RectoFace, VersoFace } from "./SheetFaces";
import { type SheetFace, SheetTitleBar } from "./SheetTitleBar";

const MESSAGE =
  "bg-night text-ink-muted flex min-h-screen items-center justify-center p-8 text-xl italic";

interface SheetScreenProps {
  readonly characterId: string;
  /** Ouvre la fiche directement en mode modification. */
  readonly initialEditing?: boolean;
}

export function SheetScreen({ characterId, initialEditing = false }: SheetScreenProps) {
  const { status, character, notice, run, dismissNotice } = useSheetController(characterId);
  const [face, setFace] = useState<SheetFace>("recto");
  const [editing, setEditing] = useState(initialEditing);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [rolling, setRolling] = useState(false);
  const [choice, setChoice] = useState<RollChoice>(EMPTY_CHOICE);

  const main = character === null ? null : mainSheet(character);
  const npc = character?.npc ?? null;
  const npcCategories = useNpcCategories(npc !== null, npc?.category_id ?? null);
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
    <SheetProvider value={{ character, sheet, editing, run, npcCategories }}>
      <div className="bg-night text-ink flex h-screen flex-col">
        <SheetTitleBar
          name={title}
          owner={character.owner_name}
          npc={
            npc === null
              ? null
              : { model: npc.model, category: categoryLabel(npcCategories, npc.category_id) }
          }
          face={face}
          onFace={setFace}
          editing={editing}
          onEditing={setEditing}
          rolling={rolling}
          onRolling={(next) => {
            setRolling(next);
            setChoice(EMPTY_CHOICE);
            if (next) {
              setFace("recto");
            }
          }}
        />
        {npc === null && (
          <FormTabs
            character={character}
            activeId={sheet.id}
            onSelect={setActiveId}
            editing={editing}
            run={run}
          />
        )}
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
          {face === "recto" &&
            (rolling ? (
              <RollModeProvider value={{ choice, onChoice: setChoice }}>
                <RectoFace />
              </RollModeProvider>
            ) : (
              <RectoFace />
            ))}
          {face === "verso" && <VersoFace />}
          {face === "notes" && <NotesFace />}
        </main>
        {rolling && (
          <RollDock
            character={character}
            sheet={sheet}
            choice={choice}
            onChoice={setChoice}
            // Seul le MJ reçoit la date de l'éveil, même absente.
            isGm={character.awakened_at !== undefined}
          />
        )}
      </div>
    </SheetProvider>
  );
}
