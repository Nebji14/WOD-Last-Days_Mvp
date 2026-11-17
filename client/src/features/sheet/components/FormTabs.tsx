"use client";

/**
 * Onglets des formes du personnage.
 *
 * Un onglet par forme, la forme principale en premier et jamais supprimable.
 * « Nouvelle forme » demande un nom puis copie la forme principale. En mode
 * modification, ✎ renomme et ✕ supprime après confirmation.
 */
import { type FormEvent, useState } from "react";

import { addForm, deleteForm, setSheetField } from "@/features/characters/api";
import type { Character, Sheet } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import type { RunAction } from "../useSheetController";
import { ConfirmDelete } from "./primitives";

const FORM_NAME_MAX = 60;
const TAB = "flex h-10 w-[214px] items-center gap-2 rounded-t-sm border border-b-0 px-3.5";
const NAME_INPUT =
  "border-line-strong bg-field text-ink focus:border-gold w-full min-w-0 rounded-xs border px-1.5 text-[15px] outline-none";

/** Libellé d'un onglet : le nom du personnage pour la forme principale, sinon celui de la forme. */
function tabLabel(sheet: Sheet): string {
  return sheet.is_main ? sheet.texts.name || sheet.form_name : sheet.form_name;
}

interface FormTabsProps {
  readonly character: Character;
  readonly activeId: string;
  readonly onSelect: (sheetId: string) => void;
  readonly editing: boolean;
  readonly run: RunAction;
}

export function FormTabs({ character, activeId, onSelect, editing, run }: FormTabsProps) {
  const text = labels.sheet;
  const [renaming, setRenaming] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const rename = (sheet: Sheet, value: string): void => {
    setRenaming(null);
    const next = value.trim();
    if (next !== "" && next !== sheet.form_name) {
      void run(() => setSheetField(sheet.id, "form_name", next, sheet.form_name));
    }
  };

  const create = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const name = String(new FormData(event.currentTarget).get("form_name") ?? "").trim();
    if (name === "") {
      return;
    }
    setCreating(false);
    void run(async () => {
      const updated = await addForm(character.id, name);
      const added = updated.sheets.find(
        (sheet) => !character.sheets.some((known) => known.id === sheet.id),
      );
      if (added !== undefined) {
        onSelect(added.id);
      }
      return updated;
    });
  };

  return (
    <nav
      aria-label={text.formsLabel}
      className="border-line flex h-12 shrink-0 items-end gap-2.5 border-b px-6"
    >
      {character.sheets.map((sheet) => {
        const active = sheet.id === activeId;
        return (
          <div
            key={sheet.id}
            className={`${TAB} ${active ? "border-gold bg-seat" : "border-line bg-panel/60"}`}
          >
            {renaming === sheet.id ? (
              <input
                autoFocus
                defaultValue={sheet.form_name}
                aria-label={text.renameForm}
                maxLength={FORM_NAME_MAX}
                onBlur={(event) => rename(sheet, event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
                className={NAME_INPUT}
              />
            ) : (
              <button
                type="button"
                aria-current={active ? "page" : undefined}
                onClick={() => onSelect(sheet.id)}
                className="min-w-0 flex-1 cursor-pointer text-left"
              >
                <span
                  className={`block truncate text-[15px] leading-4 font-semibold ${active ? "text-ink-bright" : "text-ink-muted"}`}
                >
                  {tabLabel(sheet)}
                </span>
                <span
                  className={`font-display block text-[7px] font-bold tracking-[1.5px] ${active ? "text-gold" : "text-ink-faint"}`}
                >
                  {sheet.is_main ? text.mainForm : text.otherForm}
                </span>
              </button>
            )}
            {editing && !sheet.is_main && renaming !== sheet.id && (
              <>
                <button
                  type="button"
                  aria-label={`${text.renameForm} ${sheet.form_name}`}
                  title={text.renameForm}
                  onClick={() => setRenaming(sheet.id)}
                  className="text-gold cursor-pointer text-sm hover:brightness-125"
                >
                  ✎
                </button>
                <ConfirmDelete
                  label={`${text.deleteForm} ${sheet.form_name}`}
                  question={text.confirmDeleteForm}
                  onConfirm={() => {
                    if (active) {
                      onSelect(character.sheets.find((other) => other.is_main)?.id ?? "");
                    }
                    void run(() => deleteForm(sheet.id));
                  }}
                />
              </>
            )}
          </div>
        );
      })}

      {creating ? (
        <form onSubmit={create} className="mb-1.5 flex h-8 w-[260px] items-center gap-2">
          <input
            autoFocus
            name="form_name"
            aria-label={text.newFormPlaceholder}
            placeholder={text.newFormPlaceholder}
            maxLength={FORM_NAME_MAX}
            onKeyDown={(event) => event.key === "Escape" && setCreating(false)}
            className={`${NAME_INPUT} h-8`}
          />
          <button
            type="submit"
            className="font-display text-gold cursor-pointer text-[9px] font-bold tracking-[1.5px]"
          >
            {text.add}
          </button>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="border-gold/70 font-display text-gold mb-1.5 h-8 w-40 cursor-pointer rounded-xs border border-dashed text-[8px] font-bold tracking-[2px] hover:brightness-125"
        >
          {text.newForm}
        </button>
      )}
    </nav>
  );
}
