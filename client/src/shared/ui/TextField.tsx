"use client";

/**
 * Champ de saisie avec libellé, pour les écrans de connexion et d'inscription.
 *
 * États : actif → bordure or ; en erreur → bordure rouge. Un champ de
 * type mot de passe propose la bascule « Afficher / Masquer ».
 */
import { useId, useState } from "react";

import { labels } from "@/shared/i18n";

interface TextFieldProps {
  readonly label: string;
  readonly name: string;
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly type?: "text" | "password";
  readonly placeholder?: string;
  readonly autoComplete: string;
  readonly invalid?: boolean;
  readonly disabled?: boolean;
  readonly autoFocus?: boolean;
}

export function TextField({
  label,
  name,
  value,
  onChange,
  type = "text",
  placeholder,
  autoComplete,
  invalid = false,
  disabled = false,
  autoFocus = false,
}: TextFieldProps) {
  const id = useId();
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === "password";
  const borderColor = invalid ? "border-blood-line" : "border-line focus-within:border-gold";

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-ink-muted text-[17px] leading-[21px] font-semibold">
        {label}
      </label>
      <div
        className={`bg-panel flex h-[46px] items-center rounded-xs border px-3.5 transition-colors ${borderColor}`}
      >
        <input
          id={id}
          name={name}
          type={isPassword && !revealed ? "password" : "text"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          disabled={disabled}
          aria-invalid={invalid}
          required
          spellCheck={false}
          autoCapitalize="none"
          className="text-ink placeholder:text-ink-faint h-full min-w-0 flex-1 bg-transparent text-lg font-medium outline-none placeholder:italic"
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((current) => !current)}
            aria-pressed={revealed}
            className="text-gold ml-3 cursor-pointer text-base font-semibold underline"
          >
            {revealed ? labels.auth.hidePassword : labels.auth.showPassword}
          </button>
        )}
      </div>
    </div>
  );
}
