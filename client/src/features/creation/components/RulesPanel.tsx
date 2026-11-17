"use client";

/**
 * [Panneau — Règles et aperçu] (06, US-007 · CA4) : règles de l'étape en
 * cours et valeurs de base recalculées à chaque point (RM-006, RM-007,
 * RM-010). La Défense n'apparaît qu'une fois Sports réparti (06-É3).
 */
import { labels } from "@/shared/i18n";

import { baseValues } from "../rules";
import { type CreationState, STEPS } from "../useCreationWizard";
import { CARD, SECTION_TITLE } from "./styles";

export function RulesPanel({ state }: { readonly state: CreationState }) {
  const text = labels.creation;
  const step = STEPS[state.step] ?? "identity";
  const base = baseValues(state.traits.attributes, state.traits.skills, state.effective.size);
  const skillsStarted = state.reached >= STEPS.indexOf("skills");
  const preview = [
    [text.preview.health, base.health_max],
    [text.preview.willpower, base.willpower_max],
    [text.preview.initiative, base.initiative],
    [text.preview.speed, base.speed],
    [text.preview.defense, skillsStarted ? base.defense : text.preview.defensePending],
  ] as const;

  return (
    <aside className={`${CARD} flex flex-col px-5 pt-5 pb-5`}>
      <h2 className={SECTION_TITLE}>{text.rules.title}</h2>
      <ul className="text-ink mt-3 flex flex-col gap-1.5 text-[15px]">
        {text.rules[step].map((rule) => (
          <li key={rule}>• {rule}</li>
        ))}
      </ul>
      <hr className="border-line my-5" />
      <h2 className="font-display text-gold text-[11px] font-bold tracking-[3px]">
        {text.preview.title}
      </h2>
      <dl className="mt-3 flex flex-col gap-2.5">
        {preview.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3 text-[15px]">
            <dt className="text-ink-muted">{label}</dt>
            <dd className="text-ink-bright font-bold">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="text-ink-faint mt-4 text-[13px] italic">{text.preview.note}</p>
    </aside>
  );
}
