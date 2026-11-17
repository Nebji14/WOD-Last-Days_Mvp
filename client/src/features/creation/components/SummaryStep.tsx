"use client";

/**
 * Étape 5 de la création : récapitulatif et état initial (06-É5).
 *
 * Caractéristiques, santé et volonté maximales : la base calculée est
 * proposée comme valeur effective, modifiable (RM-005). Piste vide, volonté
 * disponible au maximum, moralité 7 et expérience à 0 sont fixées par le
 * serveur (RM-008, RM-011, RM-013, RM-015, RM-017).
 */
import type { Dispatch } from "react";

import { ATTRIBUTES, CATEGORIES, type EffectiveField, SKILLS } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { baseValues } from "../rules";
import type { CreationAction, CreationState } from "../useCreationWizard";
import { SECTION_TITLE, SMALL_LABEL, STEP_HINT, STEP_TITLE } from "./styles";

const FIELDS: readonly EffectiveField[] = [
  "size",
  "speed",
  "defense",
  "initiative",
  "health_max",
  "willpower_max",
];
const BOUNDS: Readonly<Record<EffectiveField, { min: number; max: number }>> = {
  size: { min: 0, max: 99 },
  speed: { min: 0, max: 99 },
  defense: { min: 0, max: 99 },
  initiative: { min: 0, max: 99 },
  health_max: { min: 1, max: 30 },
  willpower_max: { min: 0, max: 30 },
};

interface SummaryStepProps {
  readonly state: CreationState;
  readonly dispatch: Dispatch<CreationAction>;
}

export function SummaryStep({ state, dispatch }: SummaryStepProps) {
  const text = labels.creation.summary;
  const { attributes, skills } = state.traits;
  const base = baseValues(attributes, skills, state.effective.size);
  const fieldLabel: Readonly<Record<EffectiveField, string>> = {
    ...labels.sheet.stats,
    health_max: text.healthMax,
    willpower_max: text.willpowerMax,
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto pr-2">
      <h2 className={STEP_TITLE}>{state.identity.name}</h2>
      <p className={STEP_HINT}>{text.hint}</p>

      <div className="mt-4 grid grid-cols-3 gap-4">
        {CATEGORIES.map((category) => (
          <div key={category}>
            <p className={SMALL_LABEL}>{labels.categories[category].toUpperCase()}</p>
            <p className="text-ink mt-1 text-[15px]">
              {ATTRIBUTES[category]
                .map((name) => `${labels.attributes[name]} ${attributes[name]}`)
                .join(" · ")}
            </p>
            <p className="text-ink-muted mt-1 text-sm">
              {SKILLS[category]
                .filter((name) => (skills[name] ?? 0) > 0)
                .map((name) => `${labels.skills[name]} ${skills[name]}`)
                .join(" · ")}
            </p>
          </div>
        ))}
      </div>
      <p className="text-ink-muted mt-3 text-[15px] italic">
        {state.specialties
          .map((specialty) =>
            specialty.skill === ""
              ? specialty.label
              : `${labels.skills[specialty.skill]} : ${specialty.label}`,
          )
          .join(" · ")}
      </p>

      <h3 className={`${SECTION_TITLE} mt-5 mb-2`}>{text.stats}</h3>
      <div className="grid grid-cols-[minmax(0,1fr)_60px_80px] items-center gap-x-3 gap-y-1">
        <span />
        <span className="font-display text-ink-muted text-center text-[8px] font-bold tracking-[1.2px]">
          {labels.sheet.stats.base}
        </span>
        <span className="font-display text-gold text-center text-[8px] font-bold tracking-[1.2px]">
          {labels.sheet.stats.effective}
        </span>
        {FIELDS.map((field) => (
          <EffectiveRow
            key={field}
            label={fieldLabel[field]}
            base={base[field]}
            value={state.effective[field] ?? base[field]}
            bounds={BOUNDS[field]}
            onChange={(value) => dispatch({ type: "effective", field, value })}
          />
        ))}
      </div>

      <h3 className={`${SECTION_TITLE} mt-5 mb-2`}>{text.initial}</h3>
      <ul className="text-ink text-[15px]">
        {text.initialLines.map((line) => (
          <li key={line}>• {line}</li>
        ))}
      </ul>
      <p className="text-ink-faint mt-3 text-sm italic">{text.later}</p>
    </div>
  );
}

interface EffectiveRowProps {
  readonly label: string;
  readonly base: number;
  readonly value: number;
  readonly bounds: { readonly min: number; readonly max: number };
  readonly onChange: (value: number) => void;
}

function EffectiveRow({ label, base, value, bounds, onChange }: EffectiveRowProps) {
  return (
    <>
      <span className="text-ink text-base font-semibold">{label}</span>
      <span className="text-ink-muted text-center">{base}</span>
      <input
        type="number"
        aria-label={`${label} — ${labels.sheet.stats.effective}`}
        value={value}
        min={bounds.min}
        max={bounds.max}
        onChange={(event) => {
          const next = Number.parseInt(event.target.value, 10);
          if (!Number.isNaN(next)) {
            onChange(Math.min(bounds.max, Math.max(bounds.min, next)));
          }
        }}
        className="border-line-strong bg-field text-ink-bright focus:border-gold h-7 w-16 justify-self-center rounded-xs border text-center outline-none"
      />
    </>
  );
}
