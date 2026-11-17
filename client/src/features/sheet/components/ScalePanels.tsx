"use client";

/**
 * [Panneau — Moralité] et [Panneau — Avantage surnaturel] du recto (05a) :
 * deux jauges graduées de 1 à 10, remplies de 1 jusqu'à la valeur.
 *
 * Moralité (RM-013, 05-I5) : annotations libres, chacune liée au niveau où
 * elle a été acquise.
 * Avantage surnaturel (05-I10) : commun à toutes les formes, la graduation 1
 * est toujours remplie, nom libre et facultatif. Il ne progresse qu'avec
 * l'accord du MJ : modifiable seulement en mode modification (M2).
 */
import { type FormEvent, useState } from "react";

import {
  addMoralityNote,
  deleteMoralityNote,
  setCharacterField,
  setSheetField,
  updateMoralityNote,
} from "@/features/characters/api";
import type { MoralityNote } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { ConfirmDelete, LINK_ACTION, Panel, TextValue, useSheet } from "./primitives";

const LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const;
const SCALE_VALUE = "text-ink text-[17px] font-bold";
const NOTE_FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold rounded-xs border px-1.5 text-base outline-none";

interface ScaleProps {
  readonly label: string;
  readonly value: number;
  /** Absent en consultation. */
  readonly onChange?: (value: number) => void;
}

/** Jauge graduée de 1 à 10 ; si `onChange` est fourni, cliquer une graduation fixe la valeur. */
function Scale({ label, value, onChange }: ScaleProps) {
  const box = (level: number): string =>
    `font-display flex h-6 w-[29px] items-center justify-center border text-[10px] font-bold ${
      level <= value
        ? "border-copper bg-copper-to text-ink-bright"
        : "border-line bg-panel text-ink-faint"
    }`;
  return (
    <span
      role={onChange ? "group" : "img"}
      aria-label={`${label} : ${value} / 10`}
      className="flex gap-1"
    >
      {LEVELS.map((level) =>
        onChange ? (
          <button
            key={level}
            type="button"
            aria-label={`${label} ${level}`}
            onClick={() => onChange(level)}
            className={`${box(level)} cursor-pointer hover:brightness-125`}
          >
            {level}
          </button>
        ) : (
          <span key={level} aria-hidden="true" className={box(level)}>
            {level}
          </span>
        ),
      )}
    </span>
  );
}

interface NoteFormProps {
  readonly initial: { readonly level: number; readonly body: string };
  readonly onSubmit: (level: number, body: string) => void;
  readonly onCancel: () => void;
}

function NoteForm({ initial, onSubmit, onCancel }: NoteFormProps) {
  const text = labels.sheet;
  const [level, setLevel] = useState(initial.level);
  const [body, setBody] = useState(initial.body);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (body.trim() !== "") {
      onSubmit(level, body.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <label className="text-ink-muted flex items-center gap-1.5 text-sm italic">
        {text.morality.level}
        <select
          value={level}
          onChange={(event) => setLevel(Number(event.target.value))}
          className={`${NOTE_FIELD} h-7`}
        >
          {LEVELS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <input
        type="text"
        value={body}
        onChange={(event) => setBody(event.target.value)}
        maxLength={500}
        autoFocus
        aria-label={text.morality.notePlaceholder}
        placeholder={text.morality.notePlaceholder}
        className={`${NOTE_FIELD} h-7 min-w-0 flex-1`}
      />
      <button type="submit" className={LINK_ACTION}>
        {text.save}
      </button>
      <button type="button" onClick={onCancel} className={`${LINK_ACTION} text-ink-muted`}>
        {text.cancel}
      </button>
    </form>
  );
}

/**
 * [Panneau — Moralité] (RM-013) : valeur de jeu, modifiable à tout moment
 * sur indication du MJ, comme ses annotations, sans passer en mode modification.
 */
export function MoralityPanel() {
  const { sheet, run } = useSheet();
  const text = labels.sheet.morality;
  /** Annotation en cours de saisie : `"new"`, l'identifiant d'une annotation, ou aucune. */
  const [open, setOpen] = useState<string | null>(null);

  const noteLine = (note: MoralityNote) =>
    open === note.id ? (
      <NoteForm
        initial={note}
        onCancel={() => setOpen(null)}
        onSubmit={(level, body) => {
          setOpen(null);
          void run(() => updateMoralityNote(note.id, level, body));
        }}
      />
    ) : (
      <span className="flex items-center gap-2">
        <span className="text-ink text-base font-semibold">
          {text.level} {note.level} — {note.body}
        </span>
        <button
          type="button"
          aria-label={labels.sheet.editItem}
          title={labels.sheet.editItem}
          onClick={() => setOpen(note.id)}
          className="text-gold cursor-pointer px-1 text-sm"
        >
          ✎
        </button>
        <ConfirmDelete
          label={labels.sheet.deleteItem}
          onConfirm={() => void run(() => deleteMoralityNote(note.id))}
        />
      </span>
    );

  return (
    <Panel title={text.title} aside={<span className={SCALE_VALUE}>{sheet.morality} / 10</span>}>
      <Scale
        label={text.title}
        value={sheet.morality}
        onChange={(value) =>
          void run(() => setSheetField(sheet.id, "morality", value, sheet.morality))
        }
      />
      <div className="mt-3.5 mb-1.5 flex items-center justify-between">
        <p className="font-display text-ink-muted text-[8px] font-bold tracking-[2px]">
          {text.notes}
        </p>
        {open === null && (
          <button type="button" onClick={() => setOpen("new")} className={LINK_ACTION}>
            {text.addNote}
          </button>
        )}
      </div>
      {sheet.morality_notes.length === 0 && open !== "new" && (
        <p className="text-ink-faint text-[15px] font-medium italic">{text.none}</p>
      )}
      <ul className="flex flex-col gap-1">
        {sheet.morality_notes.map((note) => (
          <li key={note.id}>{noteLine(note)}</li>
        ))}
      </ul>
      {open === "new" && (
        <NoteForm
          initial={{ level: sheet.morality, body: "" }}
          onCancel={() => setOpen(null)}
          onSubmit={(level, body) => {
            setOpen(null);
            void run(() => addMoralityNote(sheet.id, level, body));
          }}
        />
      )}
    </Panel>
  );
}

export function SupernaturalPanel() {
  const { character, editing, run } = useSheet();
  const text = labels.sheet.supernatural;
  const level = character.supernatural_level;

  return (
    <Panel
      title={text.title}
      aside={
        <span className="w-[340px]">
          <TextValue
            label={text.namePlaceholder}
            value={character.supernatural_name}
            editing={editing}
            maxLength={60}
            placeholder={text.namePlaceholder}
            onCommit={(value) =>
              void run(() =>
                setCharacterField(
                  character.id,
                  "supernatural_name",
                  value,
                  character.supernatural_name,
                ),
              )
            }
            className="text-ink block h-7 text-base leading-7 font-semibold italic"
          />
        </span>
      }
    >
      <div className="flex items-center gap-4">
        <Scale
          label={text.title}
          value={level}
          onChange={
            editing
              ? (value) =>
                  void run(() =>
                    setCharacterField(character.id, "supernatural_level", value, level),
                  )
              : undefined
          }
        />
        <span className={SCALE_VALUE}>{level} / 10</span>
      </div>
      <p className="font-display text-ink-muted mt-3.5 text-[8px] font-bold tracking-[2px]">
        {text.minimum}
      </p>
      <p className="text-ink mt-1.5 text-base font-semibold">{text.reminder}</p>
    </Panel>
  );
}
