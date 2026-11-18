"use client";

/**
 * Listes du verso : atouts, handicaps, pouvoirs, armes, armures et objets.
 *
 * Un même composant sert les six listes ; chaque type déclare ses colonnes.
 * « + Ajouter » fonctionne dans les deux modes. ✎ et ✕ sont disponibles à tout
 * moment pour l'équipement, qui change en cours de partie, et seulement en mode
 * modification pour les atouts, handicaps et pouvoirs, qui ne progressent
 * qu'avec l'accord du MJ.
 *
 * Un pouvoir, une arme ou un atout peut porter une recette de jet : le bouton
 * 🎲 de sa ligne lance alors les dés en un clic.
 */
import { type FormEvent, useState } from "react";

import { addEntry, deleteEntry, type EntryValues, updateEntry } from "@/features/characters/api";
import type { Entry, EntryKind, EntryNumberField } from "@/features/characters/model";
import { EntryRoll } from "@/features/dice/components/EntryRoll";
import { traitValue } from "@/features/dice/pool";
import {
  draftOf,
  type RecipeDraft,
  RecipeEditor,
  recipeOf,
} from "@/features/dice/components/RecipeEditor";
import { labels } from "@/shared/i18n";

import { COLUMN_LABEL, ConfirmDelete, LINK_ACTION, Panel, useSheet } from "./primitives";

/** Éléments qui peuvent porter une recette de jet. */
const ROLLABLE: ReadonlySet<EntryKind> = new Set<EntryKind>(["power", "weapon", "merit"]);

/** Listes d'équipement, modifiables sans passer en mode modification. */
const EQUIPMENT: ReadonlySet<EntryKind> = new Set<EntryKind>(["weapon", "armor", "item"]);

type TextColumn = "name" | "description" | "range";
type Column = TextColumn | EntryNumberField;

interface KindLayout {
  /** Colonnes dans l'ordre d'affichage ; la description vient toujours en dernier. */
  readonly columns: readonly Column[];
  /** Largeurs des colonnes (grille CSS). */
  readonly grid: string;
}

const LAYOUTS: Record<EntryKind, KindLayout> = {
  merit: {
    columns: ["name", "level", "description"],
    grid: "grid-cols-[150px_52px_minmax(0,1fr)]",
  },
  flaw: { columns: ["name", "level", "description"], grid: "grid-cols-[150px_52px_minmax(0,1fr)]" },
  power: {
    columns: ["name", "level", "description"],
    grid: "grid-cols-[150px_52px_minmax(0,1fr)]",
  },
  item: {
    columns: ["name", "quantity", "description"],
    grid: "grid-cols-[150px_40px_minmax(0,1fr)]",
  },
  weapon: {
    columns: ["name", "damage_modifier", "range", "size", "initiative_penalty", "description"],
    grid: "grid-cols-[130px_48px_70px_44px_40px_minmax(0,1fr)]",
  },
  armor: {
    columns: [
      "name",
      "general_protection",
      "ballistic_protection",
      "min_strength",
      "defense_penalty",
      "description",
    ],
    grid: "grid-cols-[120px_56px_56px_52px_52px_minmax(0,1fr)]",
  },
};
const TEXT_COLUMNS: readonly Column[] = ["name", "description", "range"];
const FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold h-7 w-full min-w-0 rounded-xs border px-1.5 text-[15px] outline-none";

function isText(column: Column): column is TextColumn {
  return TEXT_COLUMNS.includes(column);
}

function display(entry: Entry, column: Column): string {
  const value = entry[column];
  return value === null || value === "" ? "—" : String(value);
}

interface EntryFormProps {
  readonly kind: EntryKind;
  /** Valeur actuelle d'un trait de la fiche, pour la recette de jet. */
  readonly valueOf: (part: string) => number;
  readonly layout: KindLayout;
  readonly initial: Entry | null;
  readonly onSubmit: (values: EntryValues) => void;
  readonly onCancel: () => void;
}

function EntryForm({ kind, valueOf, layout, initial, onSubmit, onCancel }: EntryFormProps) {
  const [recipe, setRecipe] = useState<RecipeDraft>(() => draftOf(initial?.roll));
  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      layout.columns.map((column) => [column, initial ? String(initial[column] ?? "") : ""]),
    ),
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const values: Record<string, string | number | null> = {};
    for (const column of layout.columns) {
      const raw = (draft[column] ?? "").trim();
      if (isText(column)) {
        values[column] = raw;
      } else {
        const parsed = Number.parseInt(raw, 10);
        values[column] = Number.isNaN(parsed) ? null : parsed;
      }
    }
    onSubmit(ROLLABLE.has(kind) ? { ...values, roll: recipeOf(recipe) } : values);
  }

  return (
    <form onSubmit={handleSubmit} className="border-gold/50 rounded-sm border bg-[#1e1813] p-2">
      <div className={`grid items-center gap-x-2 ${layout.grid}`}>
        {layout.columns.map((column, index) => (
          <input
            key={column}
            type={isText(column) ? "text" : "number"}
            value={draft[column] ?? ""}
            onChange={(event) => setDraft({ ...draft, [column]: event.target.value })}
            aria-label={labels.sheet.columns[column]}
            placeholder={labels.sheet.columns[column]}
            maxLength={column === "description" ? 4000 : 120}
            autoFocus={index === 0}
            className={FIELD}
          />
        ))}
      </div>
      {ROLLABLE.has(kind) && (
        <RecipeEditor kind={kind} draft={recipe} onChange={setRecipe} valueOf={valueOf} />
      )}
      <div className="mt-2 flex justify-end gap-4">
        <button type="submit" className={LINK_ACTION}>
          {labels.sheet.save}
        </button>
        <button type="button" onClick={onCancel} className={`${LINK_ACTION} text-ink-muted`}>
          {labels.sheet.cancel}
        </button>
      </div>
    </form>
  );
}

export function EntryPanel({ kind }: { readonly kind: EntryKind }) {
  const { character, sheet, editing, run } = useSheet();
  const text = labels.sheet.entries[kind];
  const layout = LAYOUTS[kind];
  const entries = sheet.entries.filter((entry) => entry.kind === kind);
  const changeable = editing || EQUIPMENT.has(kind);
  /** Ligne en cours de saisie : `"new"`, l'identifiant d'un élément, ou aucune. */
  const [open, setOpen] = useState<string | null>(null);
  const valueOf = (part: string) =>
    traitValue(
      character,
      sheet,
      part,
      sheet.entries.find((entry) => entry.id === open),
    );

  return (
    <Panel
      title={text.title}
      aside={
        open === null && (
          <button type="button" onClick={() => setOpen("new")} className={LINK_ACTION}>
            {text.add}
          </button>
        )
      }
    >
      {entries.length > 0 && (
        <div className={`mb-1.5 grid gap-x-2 px-3 ${layout.grid}`}>
          {layout.columns.map((column) => (
            <span key={column} className={COLUMN_LABEL}>
              {labels.sheet.columns[column]}
            </span>
          ))}
        </div>
      )}
      <ul className="flex flex-col gap-1.5">
        {entries.map((entry) =>
          open === entry.id && changeable ? (
            <li key={entry.id}>
              <EntryForm
                kind={kind}
                valueOf={valueOf}
                layout={layout}
                initial={entry}
                onCancel={() => setOpen(null)}
                onSubmit={(values) => {
                  setOpen(null);
                  void run(() => updateEntry(entry.id, values));
                }}
              />
            </li>
          ) : (
            <li
              key={entry.id}
              className="border-line-soft bg-panel flex min-h-10 items-center rounded-sm border px-3 py-1.5"
            >
              <div className={`grid flex-1 items-baseline gap-x-2 ${layout.grid}`}>
                {layout.columns.map((column) => (
                  <span
                    key={column}
                    className={
                      column === "name"
                        ? "text-ink truncate text-base font-bold"
                        : column === "description"
                          ? "text-ink-muted text-[15px] leading-tight font-medium italic"
                          : "text-ink text-base font-semibold"
                    }
                  >
                    {display(entry, column)}
                  </span>
                ))}
              </div>
              {entry.roll != null && (
                <span className="ml-2 shrink-0">
                  <EntryRoll character={character} sheet={sheet} entry={entry} />
                </span>
              )}
              {changeable && (
                <span className="ml-2 flex shrink-0 items-center gap-1">
                  <button
                    type="button"
                    aria-label={`${labels.sheet.editItem} ${entry.name}`}
                    title={labels.sheet.editItem}
                    onClick={() => setOpen(entry.id)}
                    className="text-gold cursor-pointer px-1 text-sm hover:brightness-125"
                  >
                    ✎
                  </button>
                  <ConfirmDelete
                    label={`${labels.sheet.deleteItem} ${entry.name}`}
                    onConfirm={() => void run(() => deleteEntry(entry.id))}
                  />
                </span>
              )}
            </li>
          ),
        )}
      </ul>
      {entries.length === 0 && open !== "new" && (
        <p className="text-ink-faint text-[15px] font-medium italic">{text.empty}</p>
      )}
      {open === "new" && (
        <div className="mt-1.5">
          <EntryForm
            kind={kind}
            valueOf={valueOf}
            layout={layout}
            initial={null}
            onCancel={() => setOpen(null)}
            onSubmit={(values) => {
              setOpen(null);
              void run(() => addEntry(sheet.id, kind, values));
            }}
          />
        </div>
      )}
    </Panel>
  );
}
