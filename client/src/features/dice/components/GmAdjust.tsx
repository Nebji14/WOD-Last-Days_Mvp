/**
 * Malus et bonus annoncés par le MJ au moment du jet.
 *
 * Le malus couvre la défense ou la résistance de l'adversaire et les
 * circonstances défavorables ; le bonus, l'équipement, l'aide et les
 * circonstances favorables. Les deux se cumulent : 4 de malus et 2 de bonus
 * retirent 2 dés.
 */
import { labels } from "@/shared/i18n";

export const ADJUST_MAX = 10;

const STEP =
  "border-line-strong text-gold hover:border-gold size-7 cursor-pointer rounded-xs border text-base leading-none font-bold disabled:cursor-not-allowed disabled:opacity-35";

function Counter(props: {
  readonly label: string;
  readonly hint: string;
  readonly value: number;
  readonly sign: "−" | "+";
  readonly tone: string;
  readonly onChange: (value: number) => void;
}) {
  const { label, hint, value, sign, tone, onChange } = props;
  return (
    <span className="text-ink flex items-center gap-2 text-base" title={hint}>
      {label}
      <button
        type="button"
        aria-label={`${label} −1`}
        disabled={value <= 0}
        onClick={() => onChange(value - 1)}
        className={STEP}
      >
        −
      </button>
      <strong className={`w-8 text-center ${value > 0 ? tone : "text-ink-muted"}`}>
        {value > 0 ? `${sign}${value}` : "0"}
      </strong>
      <button
        type="button"
        aria-label={`${label} +1`}
        disabled={value >= ADJUST_MAX}
        onClick={() => onChange(value + 1)}
        className={STEP}
      >
        +
      </button>
    </span>
  );
}

interface GmAdjustProps {
  readonly malus: number;
  readonly bonus: number;
  readonly onChange: (malus: number, bonus: number) => void;
}

export function GmAdjust({ malus, bonus, onChange }: GmAdjustProps) {
  const text = labels.dice;
  return (
    <span className="flex flex-wrap items-center gap-x-5 gap-y-2">
      <Counter
        label={text.malus}
        hint={text.malusHint}
        value={malus}
        sign="−"
        tone="text-danger"
        onChange={(value) => onChange(value, bonus)}
      />
      <Counter
        label={text.bonus}
        hint={text.bonusHint}
        value={bonus}
        sign="+"
        tone="text-gold"
        onChange={(value) => onChange(malus, value)}
      />
    </span>
  );
}
