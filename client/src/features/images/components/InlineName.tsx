"use client";

/**
 * Nom modifiable sur place (04b-I5, I9) : Entrée ou sortie du champ valide,
 * Échap annule. Un nom vide ou inchangé annule aussi.
 */
import { useState } from "react";

interface InlineNameProps {
  readonly initial: string;
  readonly label: string;
  readonly maxLength: number;
  readonly onSubmit: (name: string) => void;
  readonly onCancel: () => void;
  readonly className?: string;
}

export function InlineName({
  initial,
  label,
  maxLength,
  onSubmit,
  onCancel,
  className = "",
}: InlineNameProps) {
  const [value, setValue] = useState(initial);
  const [done, setDone] = useState(false);

  const finish = (commit: boolean) => {
    if (done) {
      return;
    }
    setDone(true);
    const name = value.trim();
    if (commit && name !== "" && name !== initial) {
      onSubmit(name);
    } else {
      onCancel();
    }
  };

  return (
    <input
      type="text"
      value={value}
      aria-label={label}
      maxLength={maxLength}
      autoFocus
      onFocus={(event) => event.currentTarget.select()}
      onChange={(event) => setValue(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          finish(true);
        } else if (event.key === "Escape") {
          event.stopPropagation();
          finish(false);
        }
      }}
      onBlur={() => finish(true)}
      onClick={(event) => event.stopPropagation()}
      className={`border-gold bg-field text-ink rounded-xs border px-1.5 outline-none ${className}`}
    />
  );
}
