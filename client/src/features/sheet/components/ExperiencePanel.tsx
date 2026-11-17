"use client";

/**
 * Panneau « Expérience » du verso.
 *
 * Expérience générale et tactique suivies séparément, avec le total acquis et
 * le solde. Le total se saisit ; le solde ne baisse que par une dépense, qui
 * porte un type, des points et une justification obligatoire. Le serveur
 * refuse une dépense supérieure au solde.
 */
import { type FormEvent, useState } from "react";

import { addExpense, deleteExpense, setCharacterField } from "@/features/characters/api";
import type { Experience } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import {
  COLUMN_LABEL,
  ConfirmDelete,
  LINK_ACTION,
  NumberValue,
  Panel,
  useSheet,
} from "./primitives";

const FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold h-8 min-w-0 rounded-xs border px-1.5 text-base outline-none";

interface PoolProps {
  readonly title: string;
  readonly pool: Experience;
  readonly field: "xp_general_total" | "xp_tactical_total";
}

function Pool({ title, pool, field }: PoolProps) {
  const { character, editing, run } = useSheet();
  const text = labels.sheet.experience;

  return (
    <div className="border-line bg-panel rounded-sm border px-4 py-3">
      <p className="font-display text-gold text-[9px] font-bold tracking-[2px]">{title}</p>
      <p className="text-ink-bright mt-1 text-[30px] leading-9 font-bold">{pool.balance}</p>
      <p className="text-ink-muted text-sm font-medium italic">{text.balance}</p>
      <p className="text-ink-muted mt-1 flex items-center gap-1.5 text-sm font-medium italic">
        {text.total} :
        <NumberValue
          label={`${text.total} — ${title}`}
          value={pool.total}
          editing={editing}
          min={0}
          max={99999}
          onCommit={(value) =>
            void run(() => setCharacterField(character.id, field, value, pool.total))
          }
          className="text-ink text-base font-bold not-italic"
        />
      </p>
    </div>
  );
}

function ExpenseForm({ onClose }: { readonly onClose: () => void }) {
  const { character, run } = useSheet();
  const text = labels.sheet.experience;
  const [tactical, setTactical] = useState(false);
  const [points, setPoints] = useState("1");
  const [justification, setJustification] = useState("");
  const amount = Number.parseInt(points, 10);
  const valid = amount >= 1 && justification.trim() !== "";

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!valid) {
      return;
    }
    onClose();
    void run(() => addExpense(character.id, tactical, amount, justification.trim()));
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-gold/50 flex flex-col gap-2 rounded-sm border bg-[#1e1813] p-2.5"
    >
      <div className="flex items-center gap-2">
        <select
          value={tactical ? "tactical" : "general"}
          onChange={(event) => setTactical(event.target.value === "tactical")}
          aria-label={text.type}
          className={`${FIELD} w-[130px]`}
        >
          <option value="general">{text.typeGeneral}</option>
          <option value="tactical">{text.typeTactical}</option>
        </select>
        <input
          type="number"
          min={1}
          value={points}
          onChange={(event) => setPoints(event.target.value)}
          aria-label={text.points}
          className={`${FIELD} w-[70px] text-center`}
        />
        <input
          type="text"
          value={justification}
          onChange={(event) => setJustification(event.target.value)}
          maxLength={500}
          autoFocus
          aria-label={text.justification}
          placeholder={text.justification}
          className={`${FIELD} flex-1 placeholder:text-xs`}
        />
      </div>
      <div className="flex justify-end gap-4">
        <button
          type="submit"
          disabled={!valid}
          className={`${LINK_ACTION} disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {labels.sheet.save}
        </button>
        <button type="button" onClick={onClose} className={`${LINK_ACTION} text-ink-muted`}>
          {labels.sheet.cancel}
        </button>
      </div>
    </form>
  );
}

export function ExperiencePanel() {
  const { character, editing, run } = useSheet();
  const text = labels.sheet.experience;
  const [spending, setSpending] = useState(false);

  return (
    <Panel title={text.title}>
      <div className="grid grid-cols-2 gap-4">
        <Pool title={text.general} pool={character.xp_general} field="xp_general_total" />
        <Pool title={text.tactical} pool={character.xp_tactical} field="xp_tactical_total" />
      </div>
      {spending ? (
        <div className="mt-3.5">
          <ExpenseForm onClose={() => setSpending(false)} />
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setSpending(true)}
          className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright mt-3.5 h-9 w-full cursor-pointer rounded-xs border bg-linear-to-b text-[11px] font-bold tracking-[2px] transition hover:brightness-110"
        >
          {text.spend}
        </button>
      )}

      <p className="font-display text-gold mt-5 mb-2.5 text-[9px] font-bold tracking-[2px]">
        {text.journal}
      </p>
      {character.expenses.length === 0 ? (
        <p className="text-ink-faint text-[15px] font-medium italic">{text.noExpense}</p>
      ) : (
        <>
          <div className="mb-1 grid grid-cols-[100px_60px_minmax(0,1fr)_auto] gap-x-2">
            <span className={COLUMN_LABEL}>{text.type}</span>
            <span className={COLUMN_LABEL}>{text.points}</span>
            <span className={COLUMN_LABEL}>{text.justification}</span>
          </div>
          <ul>
            {character.expenses.map((expense) => (
              <li
                key={expense.id}
                className="grid min-h-8 grid-cols-[100px_60px_minmax(0,1fr)_auto] items-center gap-x-2"
              >
                <span className="text-ink text-base font-semibold">
                  {expense.is_tactical ? text.typeTactical : text.typeGeneral}
                </span>
                <span className="text-ink text-base font-bold">{expense.points}</span>
                <span className="text-ink-muted text-base font-medium italic">
                  {expense.justification}
                </span>
                {editing && (
                  <ConfirmDelete
                    label={`${labels.sheet.deleteItem} ${expense.justification}`}
                    onConfirm={() => void run(() => deleteExpense(expense.id))}
                  />
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="text-ink-faint mt-3 text-sm font-medium italic">{text.reminder}</p>
    </Panel>
  );
}
