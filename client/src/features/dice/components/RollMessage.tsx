/**
 * Jet de dés dans le chat : qui a lancé, la réserve, les faces de chaque
 * vague (réussites en or, dés comptés double marqués) et le résultat.
 */
import { describeParts, doubledLabel, resultLabel, successesLabel } from "../format";
import { isDoubled, isSuccess, type Roll } from "../model";

const FACE =
  "font-track inline-flex size-[18px] items-center justify-center rounded-[3px] border text-[10px] font-bold leading-none";

export function RollMessage({ roll }: { readonly roll: Roll }) {
  const counted = roll.kind !== "initiative";
  const doubled = doubledLabel(roll);
  return (
    <span className="flex flex-col gap-1">
      {roll.label != null && <span className="text-copper-light font-bold">{roll.label}</span>}
      <span className="text-ink-muted text-sm italic">{describeParts(roll.parts)}</span>
      <span className="flex flex-wrap items-center gap-1">
        {roll.stages.map((faces, stage) => (
          <span key={stage} className="flex flex-wrap gap-0.5">
            {stage > 0 && (
              <span aria-hidden="true" className="text-ink-faint px-0.5 text-xs">
                ↻
              </span>
            )}
            {faces.map((face, index) => (
              <span
                key={index}
                className={`${FACE} ${
                  counted && isDoubled(face, roll)
                    ? "border-gold bg-gold/50 text-ink-bright"
                    : counted && isSuccess(face, roll.chance)
                      ? "border-gold bg-gold/20 text-gold"
                      : "border-line text-ink-muted"
                }`}
              >
                {face}
              </span>
            ))}
          </span>
        ))}
      </span>
      <span className="font-display text-copper-light text-[11px] font-bold tracking-[2px]">
        {resultLabel(roll)}
        {counted && roll.outcome === "exceptional" && ` · ${successesLabel(roll.successes)}`}
      </span>
      {counted && doubled !== null && (
        <span className="text-gold text-sm italic">{doubled}</span>
      )}
    </span>
  );
}
