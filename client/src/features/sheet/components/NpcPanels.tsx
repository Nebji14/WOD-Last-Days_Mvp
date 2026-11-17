"use client";

/**
 * Panneaux propres à la feuille de PNJ (écran 07, US-039 à US-043).
 *
 * - [Panneau — Caractéristiques simplifiées] : Puissance, Finesse, Résilience,
 *   de 1 à 10, jamais 0 (07-I2, RM-022).
 * - [Panneau — Notes du PNJ] : notes intégrées, texte long (07-I4, US-039 · CA7).
 * - Catégorie du PNJ, modifiable en mode modification (Q04c-1, Q07-3).
 * - « Supprimer ce PNJ », en mode modification, après confirmation (US-043 · CA1).
 */
import { useState } from "react";

import type { Character } from "@/features/characters/model";
import { deleteNpc, setNpcField } from "@/features/npcs/api";
import { categoryLabel } from "@/features/npcs/categories";
import { fill, labels } from "@/shared/i18n";
import { childrenOf } from "@/shared/tree";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

import { Dots, Panel, TextValue, useSheet } from "./primitives";

const TRAITS = ["power", "finesse", "resilience"] as const;
const TRAIT_MAX = 10;
const NOTES_MAX = 20000;

export function SimplifiedTraitsPanel() {
  const { character, editing, run } = useSheet();
  const text = labels.npcSheet;
  const npc = character.npc;
  if (npc == null) {
    return null;
  }

  return (
    <Panel title={text.simplifiedTraits}>
      <div className="flex flex-col gap-1.5">
        {TRAITS.map((trait) => {
          const value = npc[trait] ?? 1;
          return (
            <div key={trait} className="grid h-8 grid-cols-[180px_1fr_40px] items-center">
              <span className="text-ink-bright text-lg font-semibold">{text.traits[trait]}</span>
              <Dots
                label={text.traits[trait]}
                value={value}
                max={TRAIT_MAX}
                min={1}
                onChange={
                  editing
                    ? (next) => void run(() => setNpcField(character.id, trait, next, value))
                    : undefined
                }
              />
              <span className="text-ink-bright text-right text-lg font-bold">{value}</span>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

export function NpcNotesPanel() {
  const { character, editing, run } = useSheet();
  const text = labels.npcSheet;
  const notes = character.npc?.notes ?? "";

  return (
    <Panel title={text.notes}>
      <TextValue
        label={text.notesLabel}
        value={notes}
        editing={editing}
        multiline
        maxLength={NOTES_MAX}
        placeholder={text.notesPlaceholder}
        onCommit={(value) => void run(() => setNpcField(character.id, "notes", value, notes))}
        className="text-ink block min-h-[280px] w-full text-[17px] leading-relaxed whitespace-pre-wrap"
      />
    </Panel>
  );
}

/** Ligne « PNJ · catégorie … » de l'identité ; liste des catégories en modification. */
export function NpcCategoryLine({ character }: { readonly character: Character }) {
  const { editing, run, npcCategories } = useSheet();
  const text = labels.npcSheet;
  const current = character.npc?.category_id ?? null;
  const label = categoryLabel(npcCategories, current) || text.noCategory;

  if (!editing) {
    return (
      <p className="text-ink-muted pl-0.5 text-[15px] font-medium italic">
        {fill(text.subtitle, { category: label })}
      </p>
    );
  }
  /** Options dans l'ordre de l'arborescence, sous-catégories en retrait. */
  const options = (parentId: string | null, depth: number): { id: string; name: string }[] =>
    childrenOf(npcCategories, parentId).flatMap((category) => [
      { id: category.id, name: `${"  ".repeat(depth)}${category.name}` },
      ...options(category.id, depth + 1),
    ]);

  return (
    <label className="text-ink-muted flex items-center gap-2 text-[15px] italic">
      {text.category}
      <select
        value={current ?? ""}
        onChange={(event) => {
          const next = event.target.value === "" ? null : event.target.value;
          void run(() => setNpcField(character.id, "category_id", next, current));
        }}
        className="border-line-strong bg-field text-ink rounded-xs border px-2 py-0.5 not-italic"
      >
        <option value="">{text.rootCategory}</option>
        {options(null, 0).map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </label>
  );
}

/** « Supprimer ce PNJ » en bas du verso, en mode modification (US-043 · CA1, CA3). */
export function NpcDeleteLink() {
  const { character, editing } = useSheet();
  const [confirming, setConfirming] = useState(false);
  const [failed, setFailed] = useState(false);
  const toolText = labels.npcsTool;
  const name = character.sheets.find((s) => s.is_main)?.texts.name ?? "";

  if (!editing || character.npc == null) {
    return null;
  }
  return (
    <div className="flex items-center justify-end gap-4 pt-2">
      {failed && <span className="text-danger text-sm">{labels.errors.internal_error}</span>}
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="font-display text-danger cursor-pointer text-[11px] font-bold tracking-[2px] hover:brightness-125"
      >
        {labels.npcSheet.deleteNpc}
      </button>
      <ConfirmDialog
        open={confirming}
        title={toolText.deleteNpcTitle}
        question={fill(toolText.deleteNpcQuestion, { name })}
        confirmLabel={toolText.confirmDelete}
        cancelLabel={toolText.cancel}
        onConfirm={() => {
          setConfirming(false);
          deleteNpc(character.id)
            .then(() => window.close())
            .catch(() => setFailed(true));
        }}
        onCancel={() => setConfirming(false)}
      />
    </div>
  );
}
