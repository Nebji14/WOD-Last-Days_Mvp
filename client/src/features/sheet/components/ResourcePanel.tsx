"use client";

/**
 * Panneau des ressources libres du recto (Mana, Douleur…).
 *
 * Chaque ressource fonctionne comme la Volonté, sans base calculée : la valeur
 * disponible se dépense à tout moment, le nom et le maximum se modifient en
 * mode modification, comme l'ajout et la suppression. Hors modification, le
 * panneau n'apparaît que si le personnage a au moins une ressource.
 */
import { type FormEvent, useState } from "react";

import { addResource, deleteResource, setResourceField } from "@/features/characters/api";
import { RESOURCE_NAME_MAX, RESOURCE_VALUE_MAX, type Resource } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

import { GaugeDots } from "./GaugeDots";
import { ConfirmDelete, LINK_ACTION, NumberValue, Panel, TextValue, useSheet } from "./primitives";

const FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold h-8 min-w-0 rounded-xs border px-1.5 text-base outline-none";
const DEFAULT_MAX = 5;

function ResourceForm({ onClose }: { readonly onClose: () => void }) {
  const { character, run } = useSheet();
  const text = labels.sheet.resources;
  const [name, setName] = useState("");
  const [max, setMax] = useState(String(DEFAULT_MAX));
  const amount = Number.parseInt(max, 10);
  const valid = name.trim() !== "" && amount >= 0 && amount <= RESOURCE_VALUE_MAX;

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!valid) {
      return;
    }
    onClose();
    void run(() => addResource(character.id, name.trim(), amount));
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-gold/50 flex flex-col gap-2 rounded-sm border bg-[#1e1813] p-2.5"
    >
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          maxLength={RESOURCE_NAME_MAX}
          autoFocus
          aria-label={text.name}
          placeholder={text.namePlaceholder}
          className={`${FIELD} flex-1`}
        />
        <input
          type="number"
          min={0}
          max={RESOURCE_VALUE_MAX}
          value={max}
          onChange={(event) => setMax(event.target.value)}
          aria-label={text.max}
          title={text.max}
          className={`${FIELD} w-[64px] text-center`}
        />
      </div>
      <div className="flex justify-end gap-4">
        <button
          type="submit"
          disabled={!valid}
          className={`${LINK_ACTION} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {labels.sheet.add}
        </button>
        <button type="button" onClick={onClose} className={`${LINK_ACTION} text-ink-muted`}>
          {labels.sheet.cancel}
        </button>
      </div>
    </form>
  );
}

function ResourceRow({ resource }: { readonly resource: Resource }) {
  const { editing, run } = useSheet();
  const text = labels.sheet.resources;
  const { id, name, max_value: max, current_value: current } = resource;

  return (
    <li className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-3">
        <TextValue
          label={text.name}
          value={name}
          editing={editing}
          maxLength={RESOURCE_NAME_MAX}
          onCommit={(next) => void run(() => setResourceField(id, "name", next, name))}
          className="font-display text-gold text-[10px] font-bold tracking-[2px]"
        />
        {editing && (
          <span className="flex shrink-0 items-center gap-1.5">
            <NumberValue
              label={`${text.max} — ${name}`}
              value={max}
              editing
              min={0}
              max={RESOURCE_VALUE_MAX}
              onCommit={(next) => void run(() => setResourceField(id, "max_value", next, max))}
            />
            <ConfirmDelete
              label={fill(text.delete, { name })}
              question={fill(text.confirmDelete, { name })}
              onConfirm={() => void run(() => deleteResource(id))}
            />
          </span>
        )}
      </div>
      <GaugeDots
        label={name}
        summary={fill(labels.sheet.willpower.available, { current, max })}
        current={current}
        max={max}
        onChange={(next) => void run(() => setResourceField(id, "current_value", next, current))}
      />
    </li>
  );
}

export function ResourcePanel() {
  const { character, editing } = useSheet();
  const text = labels.sheet.resources;
  const [adding, setAdding] = useState(false);

  if (!editing && character.resources.length === 0) {
    return null;
  }
  return (
    <Panel
      title={text.title}
      aside={
        editing &&
        !adding && (
          <button type="button" onClick={() => setAdding(true)} className={LINK_ACTION}>
            {text.add}
          </button>
        )
      }
    >
      {character.resources.length === 0 && !adding && (
        <p className="text-ink-faint text-[15px] font-medium italic">{text.hint}</p>
      )}
      <ul className="flex flex-col gap-3">
        {character.resources.map((resource) => (
          <ResourceRow key={resource.id} resource={resource} />
        ))}
      </ul>
      {adding && (
        <div className={character.resources.length > 0 ? "mt-3" : ""}>
          <ResourceForm onClose={() => setAdding(false)} />
        </div>
      )}
    </Panel>
  );
}
