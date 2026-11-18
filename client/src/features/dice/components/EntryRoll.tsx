"use client";

/**
 * Bouton 🎲 d'un pouvoir, d'une arme ou d'un atout qui a une recette de jet.
 *
 * Il ouvre un petit panneau : la réserve calculée depuis la fiche, les coûts
 * en Volonté et en ressource libre, et les réglages restants : la spécialité,
 * si le MJ l'accorde, puis le malus et le bonus qu'il annonce (défense ou
 * résistance de la cible, circonstances).
 */
import { useState } from "react";

import type { Character, Entry, Sheet } from "@/features/characters/model";
import { ApiError } from "@/shared/api/client";
import { errorLabel, fill, labels } from "@/shared/i18n";

import { startRoll } from "../api";
import { describeParts } from "../format";
import { poolSize } from "../model";
import { recipeParts } from "../pool";
import { GmAdjust } from "./GmAdjust";
import { SpecialtyOption } from "./SpecialtyOption";

interface EntryRollProps {
  readonly character: Character;
  readonly sheet: Sheet;
  readonly entry: Entry;
}

export function EntryRoll({ character, sheet, entry }: EntryRollProps) {
  const text = labels.dice;
  const [open, setOpen] = useState(false);
  const [adjust, setAdjust] = useState({ malus: 0, bonus: 0 });
  const [specialty, setSpecialty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cost = entry.roll?.willpower_cost ?? 0;
  const resource = character.resources.find((r) => r.id === entry.roll?.resource_id);
  const resourceCost = resource === undefined ? 0 : (entry.roll?.resource_cost ?? 0);
  const parts = recipeParts(character, sheet, entry, adjust);
  const size = poolSize(parts);
  const enoughWillpower = sheet.willpower_current >= cost;
  const enoughResource = resource === undefined || resource.current_value >= resourceCost;
  const affordable = enoughWillpower && enoughResource;
  const rollLabel = fill(text.recipe.roll, { name: entry.name });

  async function roll(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      await startRoll({
        kind: "entry",
        character_id: character.id,
        sheet_id: sheet.id,
        entry_id: entry.id,
        specialty,
        modifier: -adjust.malus,
        gm_bonus: adjust.bonus,
      });
      setOpen(false);
      setAdjust({ malus: 0, bonus: 0 });
      setSpecialty(false);
    } catch (caught) {
      setError(errorLabel(caught instanceof ApiError ? caught.code : "internal_error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="relative">
      <button
        type="button"
        aria-label={rollLabel}
        aria-expanded={open}
        title={describeParts(parts)}
        onClick={() => setOpen(!open)}
        className="text-gold cursor-pointer px-1 text-base hover:brightness-125"
      >
        🎲
      </button>
      {open && (
        <div className="border-gold/60 bg-panel absolute top-8 right-0 z-30 flex w-[340px] flex-col gap-3 rounded-md border p-4 shadow-[0_10px_32px_rgb(0_0_0/0.7)]">
          <p className="font-display text-gold text-[11px] font-bold tracking-[3px]">
            {entry.name.toUpperCase()}
          </p>
          <p className="text-ink text-base">
            {describeParts(parts)} ={" "}
            <strong className="text-gold">
              {size === 0
                ? text.chanceDie
                : size === 1
                  ? text.poolOne
                  : fill(text.pool, { count: size })}
            </strong>
          </p>
          {cost > 0 && (
            <p className={`text-sm italic ${enoughWillpower ? "text-copper-light" : "text-danger"}`}>
              {enoughWillpower ? fill(text.recipe.costNote, { cost }) : text.recipe.notEnough}
            </p>
          )}
          {resource !== undefined && resourceCost > 0 && (
            <p className={`text-sm italic ${enoughResource ? "text-copper-light" : "text-danger"}`}>
              {fill(enoughResource ? text.recipe.resourceNote : text.recipe.notEnoughResource, {
                cost: resourceCost,
                name: resource.name,
              })}
            </p>
          )}
          <SpecialtyOption compact checked={specialty} onChange={() => setSpecialty(!specialty)} />
          <GmAdjust
            malus={adjust.malus}
            bonus={adjust.bonus}
            onChange={(malus, bonus) => setAdjust({ malus, bonus })}
          />
          {error !== null && <p className="text-danger text-sm">{error}</p>}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="font-display text-ink-muted cursor-pointer text-[10px] font-bold tracking-[2px]"
            >
              {labels.sheet.cancel}
            </button>
            <button
              type="button"
              disabled={busy || !affordable}
              onClick={() => void roll()}
              className="font-display h-9 cursor-pointer rounded-xs border border-[#D8352C] bg-gradient-to-b from-[#B3261F] to-[#7A1512] px-6 text-xs font-bold tracking-[3px] text-white hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {text.roll}
            </button>
          </div>
        </div>
      )}
    </span>
  );
}
