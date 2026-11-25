"use client";

/** Portrait de la forme affichée, modifiable en mode modification. */
import { useState } from "react";

import { Portrait } from "@/features/characters/components/Portrait";
import { PortraitPicker } from "@/features/characters/components/PortraitPicker";
import { type PortraitFiles, removePortrait, setPortrait } from "@/features/characters/portrait";

import { useSheet } from "./primitives";

const MEDALLION = "size-[76px] text-[24px]";

export function SheetPortrait() {
  const { sheet, editing, run } = useSheet();
  const [sending, setSending] = useState(false);
  const name = sheet.texts.name ?? "";

  if (!editing) {
    return <Portrait portrait={sheet.portrait} name={name} className={MEDALLION} />;
  }

  function save(files: PortraitFiles): void {
    setSending(true);
    void run(() => setPortrait(sheet.id, files)).finally(() => setSending(false));
  }

  return (
    <PortraitPicker
      portrait={sheet.portrait}
      name={name}
      className={MEDALLION}
      busy={sending}
      compact
      onSave={save}
      onRemove={() => void run(() => removePortrait(sheet.id))}
    />
  );
}
