"use client";

/**
 * Fil d'avancement de la création : étape faite = pastille or ✓, étape en
 * cours = contour or, étape à venir = grisée. Un clic sur une étape déjà
 * atteinte y revient.
 */
import { labels } from "@/shared/i18n";

import { STEPS } from "../useCreationWizard";

interface StepTrailProps {
  readonly step: number;
  readonly reached: number;
  readonly onGoto: (step: number) => void;
}

export function StepTrail({ step, reached, onGoto }: StepTrailProps) {
  const text = labels.creation;

  return (
    <ol aria-label={text.stepsLabel} className="relative flex justify-between px-12 pt-5">
      <span aria-hidden="true" className="bg-line absolute top-[36px] right-24 left-24 h-px" />
      {STEPS.map((name, index) => {
        const current = index === step;
        const done = !current && index <= reached;
        return (
          <li key={name} className="relative z-10 flex w-28 flex-col items-center gap-2">
            <button
              type="button"
              disabled={!done}
              aria-current={current ? "step" : undefined}
              onClick={() => onGoto(index)}
              className={`flex size-8 items-center justify-center rounded-full border text-sm font-bold ${
                current
                  ? "border-gold bg-night text-ink-bright shadow-[0_0_12px_rgb(201_176_106/0.5)]"
                  : done
                    ? "border-gold bg-gold text-abyss cursor-pointer"
                    : "border-line-strong bg-night text-ink-faint"
              }`}
            >
              {done ? "✓" : index + 1}
            </button>
            <span
              className={`font-display text-[9px] font-bold tracking-[2px] ${
                current ? "text-ink" : done ? "text-gold" : "text-ink-faint"
              }`}
            >
              {text.steps[name]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
