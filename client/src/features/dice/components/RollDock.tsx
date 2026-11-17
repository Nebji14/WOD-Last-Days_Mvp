"use client";

/**
 * Panneau de jet, en bas de la fiche en mode jet.
 *
 * Il montre la réserve composée par les clics sur la fiche (malus de blessure
 * compris), les options (spécialité, volonté, malus ou bonus annoncé par le MJ,
 * relance, action assurée, jet secret pour le MJ) et les jets en un clic :
 * initiative et jet pour rester conscient.
 */
import { useState } from "react";

import type { Character, Sheet } from "@/features/characters/model";
import { ApiError } from "@/shared/api/client";
import { errorLabel, fill, labels } from "@/shared/i18n";

import { type RollRequest, startRoll } from "../api";
import { describeParts } from "../format";
import { poolSize } from "../model";
import {
  canUseSpecialty,
  EMPTY_CHOICE,
  MODIFIER_MAX,
  MODIFIER_MIN,
  previewParts,
  type RollChoice,
} from "../pool";

const OPTION = "text-ink flex items-center gap-2 text-[15px] select-none";
const SMALL_BUTTON =
  "border-line-strong font-display text-ink hover:border-gold h-8 cursor-pointer rounded-xs border px-3 text-[10px] font-bold tracking-[2px] disabled:cursor-not-allowed disabled:opacity-40";
const STATUS_MS = 3000;

interface RollDockProps {
  readonly character: Character;
  readonly sheet: Sheet;
  readonly choice: RollChoice;
  readonly onChoice: (choice: RollChoice) => void;
  /** Le lecteur est le MJ : le jet secret lui est proposé. */
  readonly isGm: boolean;
}

export function RollDock({ character, sheet, choice, onChoice, isGm }: RollDockProps) {
  const text = labels.dice;
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const parts = previewParts(character, sheet, choice);
  const size = poolSize(parts);
  const simplified = character.npc?.model === "simplified";
  const ready = choice.attribute !== null || choice.trait !== null;
  const set = (change: Partial<RollChoice>) => onChoice({ ...choice, ...change });
  const target = { character_id: character.id, sheet_id: sheet.id };

  async function send(request: RollRequest, reset: boolean): Promise<void> {
    setBusy(true);
    setStatus(null);
    try {
      await startRoll(request);
      setStatus(text.rolling);
      window.setTimeout(() => setStatus(null), STATUS_MS);
      if (reset) {
        onChoice(EMPTY_CHOICE);
      }
    } catch (error) {
      setStatus(errorLabel(error instanceof ApiError ? error.code : "internal_error"));
    } finally {
      setBusy(false);
    }
  }

  function rollChoice(): void {
    void send(
      {
        kind: choice.trait === null ? "pool" : "trait",
        ...target,
        attribute: choice.attribute ?? undefined,
        second: choice.second ?? undefined,
        trait: choice.trait ?? undefined,
        specialty: choice.specialty,
        willpower: choice.willpower,
        modifier: choice.modifier,
        again: choice.again,
        rote: choice.rote,
        secret: isGm && choice.secret,
      },
      true,
    );
  }

  return (
    <section
      aria-label={text.panelTitle}
      className="border-gold/60 bg-panel flex shrink-0 flex-col gap-3 border-t px-8 py-3.5 shadow-[0_-8px_24px_rgb(0_0_0/0.45)]"
    >
      <div className="flex items-baseline justify-between gap-6">
        <p className="font-display text-gold text-[11px] font-bold tracking-[3px]">
          {text.panelTitle}
        </p>
        <p className="text-ink min-w-0 flex-1 truncate text-right text-lg">
          {ready ? (
            <>
              {describeParts(parts)} ={" "}
              <strong className="text-gold">
                {size === 0
                  ? text.chanceDie
                  : size === 1
                    ? text.poolOne
                    : fill(text.pool, { count: size })}
              </strong>
            </>
          ) : (
            <span className="text-ink-muted italic">
              {simplified ? text.pickTraitHint : text.pickHint}
            </span>
          )}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        {canUseSpecialty(sheet, choice.second) && (
          <label className={OPTION}>
            <input
              type="checkbox"
              checked={choice.specialty}
              onChange={() => set({ specialty: !choice.specialty })}
            />
            {text.specialty}
          </label>
        )}
        <label className={OPTION} title={sheet.willpower_current < 1 ? text.noWillpower : ""}>
          <input
            type="checkbox"
            checked={choice.willpower}
            disabled={sheet.willpower_current < 1}
            onChange={() => set({ willpower: !choice.willpower })}
          />
          {text.willpower}
        </label>
        <span className={OPTION}>
          {text.modifier}
          <button
            type="button"
            aria-label={`${text.modifier} −1`}
            disabled={choice.modifier <= MODIFIER_MIN}
            onClick={() => set({ modifier: choice.modifier - 1 })}
            className={SMALL_BUTTON}
          >
            −
          </button>
          <strong
            className={`w-8 text-center ${choice.modifier < 0 ? "text-danger" : "text-gold"}`}
          >
            {choice.modifier > 0 ? `+${choice.modifier}` : choice.modifier}
          </strong>
          <button
            type="button"
            aria-label={`${text.modifier} +1`}
            disabled={choice.modifier >= MODIFIER_MAX}
            onClick={() => set({ modifier: choice.modifier + 1 })}
            className={SMALL_BUTTON}
          >
            +
          </button>
        </span>
        <label className={OPTION}>
          {text.again}
          <select
            value={choice.again}
            onChange={(event) => set({ again: Number(event.target.value) as RollChoice["again"] })}
            className="border-line-strong bg-panel text-ink h-8 rounded-xs border px-2"
          >
            {([10, 9, 8] as const).map((value) => (
              <option key={value} value={value}>
                {text.againLabels[value]}
              </option>
            ))}
          </select>
        </label>
        <label className={OPTION}>
          <input
            type="checkbox"
            checked={choice.rote}
            onChange={() => set({ rote: !choice.rote })}
          />
          {text.rote}
        </label>
        {isGm && (
          <label className={OPTION}>
            <input
              type="checkbox"
              checked={choice.secret}
              onChange={() => set({ secret: !choice.secret })}
            />
            {text.secret}
          </label>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={!ready || busy}
          onClick={rollChoice}
          className="font-display h-10 cursor-pointer rounded-xs border border-[#D8352C] bg-gradient-to-b from-[#B3261F] to-[#7A1512] px-8 text-xs font-bold tracking-[3px] text-white shadow-[0_0_18px_rgb(179_38_31/0.45)] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {text.roll}
        </button>
        {!simplified && (
          <>
            <button
              type="button"
              disabled={busy}
              onClick={() => void send({ kind: "initiative", ...target }, false)}
              className={SMALL_BUTTON}
            >
              {text.initiative}
            </button>
            <button
              type="button"
              title={text.consciousnessHint}
              disabled={busy}
              onClick={() =>
                void send({ kind: "consciousness", ...target, modifier: choice.modifier }, false)
              }
              className={SMALL_BUTTON}
            >
              {text.consciousness}
            </button>
          </>
        )}
        <button
          type="button"
          disabled={busy}
          onClick={() => onChoice(EMPTY_CHOICE)}
          className={SMALL_BUTTON}
        >
          {text.clear}
        </button>
        {status !== null && (
          <p role="status" className="text-copper-light text-[15px] italic">
            {status}
          </p>
        )}
      </div>
    </section>
  );
}
