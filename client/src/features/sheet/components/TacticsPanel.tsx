"use client";

/**
 * [Panneau — Tactiques] du verso (05b).
 *
 * Une tactique peut être partagée entre plusieurs personnages. « + Ajouter »
 * propose donc d'en choisir une existante ou d'en créer une nouvelle (Q05-3).
 * Modifier une tactique la change pour tous ceux qui la connaissent ; la
 * retirer de la fiche ne la supprime pas chez les autres.
 */
import { type FormEvent, useEffect, useState } from "react";

import {
  createTactic,
  fetchTactics,
  linkTactic,
  removeTactic,
  updateTactic,
} from "@/features/characters/api";
import type { Tactic } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { ConfirmDelete, LINK_ACTION, Panel, useSheet } from "./primitives";

const FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold h-7 min-w-0 rounded-xs border px-1.5 text-[15px] outline-none";

interface TacticFormProps {
  readonly initial: { readonly name: string; readonly description: string };
  readonly onSubmit: (name: string, description: string) => void;
  readonly onCancel: () => void;
}

function TacticForm({ initial, onSubmit, onCancel }: TacticFormProps) {
  const [name, setName] = useState(initial.name);
  const [description, setDescription] = useState(initial.description);
  const columns = labels.sheet.columns;

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (name.trim() !== "") {
      onSubmit(name.trim(), description.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        maxLength={120}
        autoFocus
        aria-label={columns.name}
        placeholder={columns.name}
        className={`${FIELD} w-[150px]`}
      />
      <input
        type="text"
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        maxLength={4000}
        aria-label={columns.description}
        placeholder={columns.description}
        className={`${FIELD} flex-1`}
      />
      <button type="submit" className={LINK_ACTION}>
        {labels.sheet.save}
      </button>
      <button type="button" onClick={onCancel} className={`${LINK_ACTION} text-ink-muted`}>
        {labels.sheet.cancel}
      </button>
    </form>
  );
}

/** Choix d'une tactique existante, ou création d'une nouvelle. */
function TacticPicker({ onClose }: { readonly onClose: () => void }) {
  const { sheet, run } = useSheet();
  const text = labels.sheet.tactics;
  const [available, setAvailable] = useState<readonly Tactic[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchTactics()
      .then((tactics) => {
        if (!cancelled) {
          setAvailable(tactics);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const known = new Set(sheet.tactics.map((tactic) => tactic.id));
  const others = available.filter((tactic) => !known.has(tactic.id));

  return (
    <div className="border-gold/50 mt-1.5 flex flex-col gap-2 rounded-sm border bg-[#1e1813] p-2">
      {others.length > 0 && (
        <div className="flex items-center gap-2">
          <select
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
            aria-label={text.existing}
            className={`${FIELD} flex-1`}
          >
            <option value="">{text.existing}</option>
            {others.map((tactic) => (
              <option key={tactic.id} value={tactic.id}>
                {tactic.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={selected === ""}
            onClick={() => {
              onClose();
              void run(() => linkTactic(sheet.id, selected));
            }}
            className={`${LINK_ACTION} disabled:cursor-not-allowed disabled:opacity-40`}
          >
            {labels.sheet.add}
          </button>
        </div>
      )}
      {others.length > 0 && <p className="text-ink-muted text-sm italic">{text.create}</p>}
      <TacticForm
        initial={{ name: "", description: "" }}
        onCancel={onClose}
        onSubmit={(name, description) => {
          onClose();
          void run(() => createTactic(sheet.id, name, description));
        }}
      />
    </div>
  );
}

export function TacticsPanel() {
  const { sheet, editing, run } = useSheet();
  const text = labels.sheet.tactics;
  /** Saisie en cours : `"new"`, l'identifiant d'une tactique, ou aucune. */
  const [open, setOpen] = useState<string | null>(null);

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
      <ul className="flex flex-col gap-1.5">
        {sheet.tactics.map((tactic) => (
          <li
            key={tactic.id}
            className="border-line-soft bg-panel min-h-10 rounded-sm border px-3 py-1.5"
          >
            {open === tactic.id && editing ? (
              <>
                <TacticForm
                  initial={tactic}
                  onCancel={() => setOpen(null)}
                  onSubmit={(name, description) => {
                    setOpen(null);
                    void run(() => updateTactic(sheet.id, tactic.id, name, description));
                  }}
                />
                <p className="text-ink-faint mt-1 text-[13px] italic">{text.shared}</p>
              </>
            ) : (
              <div className="flex items-baseline gap-3">
                <span className="text-ink w-[150px] shrink-0 truncate text-base font-bold">
                  {tactic.name || "—"}
                </span>
                <span className="text-ink-muted flex-1 text-[15px] leading-tight font-medium italic">
                  {tactic.description}
                </span>
                {editing && (
                  <span className="flex shrink-0 items-center gap-1">
                    <button
                      type="button"
                      aria-label={`${labels.sheet.editItem} ${tactic.name}`}
                      title={labels.sheet.editItem}
                      onClick={() => setOpen(tactic.id)}
                      className="text-gold cursor-pointer px-1 text-sm hover:brightness-125"
                    >
                      ✎
                    </button>
                    <ConfirmDelete
                      label={`${labels.sheet.deleteItem} ${tactic.name}`}
                      onConfirm={() => void run(() => removeTactic(sheet.id, tactic.id))}
                    />
                  </span>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
      {sheet.tactics.length === 0 && open !== "new" && (
        <p className="text-ink-faint text-[15px] font-medium italic">{text.empty}</p>
      )}
      {open === "new" && <TacticPicker onClose={() => setOpen(null)} />}
    </Panel>
  );
}
