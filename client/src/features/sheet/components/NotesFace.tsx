"use client";

/**
 * Face NOTES de la fiche (05c, N1 à N5).
 *
 * Les notes sont communes à toutes les formes du personnage (Q05-8).
 * Le propriétaire les crée, les modifie et les supprime ; le MJ les lit
 * seulement (`can_manage_notes`, contrôlé par le serveur).
 * Saisie directe enregistrée automatiquement, peu après la frappe et en
 * quittant le champ : rien n'est perdu à la fermeture (N4).
 */
import { useEffect, useRef, useState } from "react";

import { addNote, deleteNote, updateNote } from "@/features/characters/api";
import type { Note } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

import { ConfirmDelete, PANEL, PANEL_TITLE, SMALL_LABEL, useSheet } from "./primitives";

const AUTOSAVE_DELAY_MS = 800;
const TITLE_MAX = 120;
const BODY_MAX = 20000;
const FIELD =
  "border-line-strong bg-field-deep text-ink focus:border-gold w-full rounded-xs border px-3 outline-none read-only:cursor-default";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

function newestFirst(notes: readonly Note[]): Note[] {
  return [...notes].sort((left, right) => right.updated_at.localeCompare(left.updated_at));
}

export function NotesFace() {
  const { character, run } = useSheet();
  const text = labels.sheet.notes;
  const notes = newestFirst(character.notes);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = notes.find((note) => note.id === selectedId) ?? notes[0] ?? null;
  const count = notes.length === 1 ? text.one : fill(text.count, { count: notes.length });

  const create = (): void => {
    void run(async () => {
      const { character: updated, noteId } = await addNote(character.id);
      setSelectedId(noteId);
      return updated;
    });
  };

  return (
    <div className="grid h-full grid-cols-[360px_minmax(0,1fr)] gap-4">
      <section className={`${PANEL} flex min-h-0 flex-col px-4 pt-4 pb-4`}>
        <h2 className={`${PANEL_TITLE} mb-3 px-1`}>
          {text.title} · {count}
        </h2>
        {character.can_manage_notes && (
          <button
            type="button"
            onClick={create}
            className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright mb-4 h-9 w-full shrink-0 cursor-pointer rounded-xs border bg-linear-to-b text-[11px] font-bold tracking-[2px] hover:brightness-110"
          >
            + {text.create}
          </button>
        )}
        {notes.length === 0 && (
          <p className="text-ink-faint px-1 text-[15px] italic">{text.none}</p>
        )}
        <ul className="flex min-h-0 flex-col gap-2.5 overflow-y-auto">
          {notes.map((note) => (
            <li key={note.id}>
              <button
                type="button"
                aria-current={note.id === selected?.id ? "true" : undefined}
                onClick={() => setSelectedId(note.id)}
                className={`w-full cursor-pointer rounded-xs border px-3 py-2 text-left ${
                  note.id === selected?.id ? "border-gold bg-field" : "border-line-soft"
                }`}
              >
                <span className="text-ink-bright block truncate text-base font-semibold">
                  {note.title || text.untitled}
                </span>
                <span className="text-ink-muted block truncate text-sm italic">
                  {note.body.split("\n")[0]}
                </span>
                <span className="font-display text-ink-faint block text-[7px] font-bold tracking-[1.5px] uppercase">
                  {fill(text.modified, { date: formatDate(note.updated_at) })}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className={`${PANEL} flex min-h-0 flex-col px-6 pt-5 pb-5`}>
        {selected === null ? (
          <p className="text-ink-faint text-[15px] italic">{text.select}</p>
        ) : (
          <NoteEditor key={selected.id} note={selected} editable={character.can_manage_notes} />
        )}
      </section>
    </div>
  );
}

interface Draft {
  readonly title: string;
  readonly body: string;
}

interface NoteEditorProps {
  readonly note: Note;
  readonly editable: boolean;
}

/**
 * [Panneau — Éditeur de note] (N3).
 *
 * Sans saisie en attente, l'éditeur affiche la note du serveur : une
 * modification faite depuis une autre fenêtre apparaît en direct. Une saisie
 * en cours est gardée en brouillon jusqu'à son enregistrement, sans être
 * écrasée.
 */
function NoteEditor({ note, editable }: NoteEditorProps) {
  const { run } = useSheet();
  const text = labels.sheet.notes;
  const [draft, setDraft] = useState<Draft | null>(null);
  const draftRef = useRef<Draft | null>(null);
  const timerRef = useRef<number | null>(null);
  const title = draft?.title ?? note.title;
  const body = draft?.body ?? note.body;

  const flush = (): void => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    const sent = draftRef.current;
    if (sent === null) {
      return;
    }
    void run(() => updateNote(note.id, sent.title, sent.body)).then(() => {
      if (draftRef.current === sent) {
        draftRef.current = null;
        setDraft(null);
      }
    });
  };

  const flushRef = useRef(flush);
  useEffect(() => {
    flushRef.current = flush;
  });

  useEffect(() => {
    const onHide = (): void => flushRef.current();
    window.addEventListener("pagehide", onHide);
    return () => {
      window.removeEventListener("pagehide", onHide);
      onHide();
    };
  }, []);

  const change = (next: Partial<Draft>): void => {
    const updated = { title, body, ...draftRef.current, ...next };
    draftRef.current = updated;
    setDraft(updated);
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(flush, AUTOSAVE_DELAY_MS);
  };

  return (
    <>
      <label htmlFor="note-title" className={SMALL_LABEL}>
        {text.titleLabel}
      </label>
      <input
        id="note-title"
        value={title}
        readOnly={!editable}
        maxLength={TITLE_MAX}
        placeholder={text.untitled}
        onChange={(event) => change({ title: event.target.value })}
        onBlur={flush}
        className={`${FIELD} text-ink-bright mt-1.5 mb-5 h-11 text-[22px] font-semibold`}
      />
      <label htmlFor="note-body" className={SMALL_LABEL}>
        {text.bodyLabel}
      </label>
      <textarea
        id="note-body"
        value={body}
        readOnly={!editable}
        maxLength={BODY_MAX}
        placeholder={text.bodyPlaceholder}
        onChange={(event) => change({ body: event.target.value })}
        onBlur={flush}
        className={`${FIELD} mt-1.5 min-h-0 flex-1 resize-none py-3 text-[17px] leading-[26px]`}
      />
      <footer className="mt-5 flex items-center justify-between gap-4">
        <p className="text-ink-faint text-sm italic">
          {!editable
            ? text.readOnly
            : draft !== null
              ? text.pending
              : fill(text.saved, { date: formatDate(note.updated_at) })}
        </p>
        {editable && (
          <ConfirmDelete
            label={text.delete}
            question={text.confirmDelete}
            trigger={text.delete.toUpperCase()}
            onConfirm={() => void run(() => deleteNote(note.id))}
          />
        )}
      </footer>
    </>
  );
}
