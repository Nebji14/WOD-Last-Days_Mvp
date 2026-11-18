"use client";

/**
 * Dés libres du MJ, depuis la table : un nombre de dés, la relance, la
 * spécialité, l'action assurée et, au choix, un jet secret montré au MJ seul.
 */
import { useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorLabel, labels } from "@/shared/i18n";

import { startRoll } from "../api";
import { SpecialtyOption } from "./SpecialtyOption";

const FIELD =
  "border-line-strong bg-panel text-ink focus:border-gold h-8 rounded-xs border px-2 text-[15px] outline-none";
const LABEL = "font-display text-ink-muted text-[9px] font-bold tracking-[2px]";
const MAX_DICE = 30;

export function GmDice() {
  const text = labels.dice;
  const [open, setOpen] = useState(false);
  const [dice, setDice] = useState(5);
  const [again, setAgain] = useState<8 | 9 | 10>(10);
  const [rote, setRote] = useState(false);
  const [specialty, setSpecialty] = useState(false);
  const [secret, setSecret] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function roll(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await startRoll({ kind: "free", dice, again, specialty, rote, secret });
      setOpen(false);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.code : "internal_error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="absolute bottom-3.5 left-4 z-20 flex flex-col items-start gap-2">
      {open && (
        <div className="border-line bg-panel flex w-[260px] flex-col gap-3 rounded-md border p-4 shadow-[0_8px_32px_rgb(0_0_0/0.6)]">
          <p className="font-display text-gold text-[11px] font-bold tracking-[3px]">
            {text.freeTitle}
          </p>
          <label className="flex items-center justify-between gap-3">
            <span className={LABEL}>{text.freeDice}</span>
            <input
              type="number"
              min={1}
              max={MAX_DICE}
              value={dice}
              onChange={(event) =>
                setDice(Math.min(MAX_DICE, Math.max(1, Number(event.target.value) || 1)))
              }
              className={`${FIELD} w-16 text-center`}
            />
          </label>
          <label className="flex items-center justify-between gap-3">
            <span className={LABEL}>{text.again}</span>
            <select
              value={again}
              onChange={(event) => setAgain(Number(event.target.value) as 8 | 9 | 10)}
              className={FIELD}
            >
              {([10, 9, 8] as const).map((value) => (
                <option key={value} value={value}>
                  {text.againLabels[value]}
                </option>
              ))}
            </select>
          </label>
          <SpecialtyOption compact checked={specialty} onChange={() => setSpecialty(!specialty)} />
          <label className="text-ink flex items-center gap-2 text-[15px]">
            <input type="checkbox" checked={rote} onChange={() => setRote(!rote)} />
            {text.rote}
          </label>
          <label className="text-ink flex items-center gap-2 text-[15px]">
            <input type="checkbox" checked={secret} onChange={() => setSecret(!secret)} />
            {text.secret}
          </label>
          {error !== null && <p className="text-danger text-sm">{errorLabel(error)}</p>}
          <button
            type="button"
            disabled={busy}
            onClick={() => void roll()}
            className="font-display cursor-pointer rounded-xs border border-[#D8352C] bg-gradient-to-b from-[#B3261F] to-[#7A1512] py-2 text-xs font-bold tracking-[3px] text-white hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
          >
            {text.roll}
          </button>
        </div>
      )}
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="border-gold bg-panel font-display text-ink hover:border-gold flex h-10 cursor-pointer items-center gap-2 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125"
      >
        <span aria-hidden="true" className="text-gold text-base">
          ⚄
        </span>
        {text.open}
      </button>
    </div>
  );
}
