"use client";

/**
 * Champ de recherche avec suggestions. Flèches pour parcourir, Entrée pour
 * lancer la suggestion choisie ou le texte saisi, Échap pour refermer.
 */
import { type KeyboardEvent, useId, useState } from "react";

import { labels } from "@/shared/i18n";

import { FIELD } from "./styles";

interface SuggestionFieldProps {
  readonly value: string;
  readonly maxLength: number;
  readonly suggestions: readonly string[];
  readonly onChange: (value: string) => void;
  /** Suggestion choisie : la recherche part aussitôt. */
  readonly onPick: (suggestion: string) => void;
}

export function SuggestionField(props: SuggestionFieldProps) {
  const { value, suggestions } = props;
  const text = labels.musicTool;
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const shown = open && suggestions.length > 0;
  const current = shown ? suggestions[active] : undefined;

  const close = () => {
    setOpen(false);
    setActive(-1);
  };

  const pick = (suggestion: string) => {
    close();
    props.onPick(suggestion);
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      if (suggestions.length > 0) {
        // Le cran -1 rend la main au texte saisi.
        const step = event.key === "ArrowDown" ? 1 : -1;
        const count = suggestions.length + 1;
        setActive(((active + 1 + step + count) % count) - 1);
      }
    } else if (event.key === "Escape" && shown) {
      event.preventDefault();
      close();
    } else if (event.key === "Enter") {
      if (current !== undefined) {
        event.preventDefault();
        pick(current);
      } else {
        close();
      }
    }
  };

  return (
    <div className="relative min-w-0 flex-1">
      <input
        type="search"
        role="combobox"
        value={value}
        maxLength={props.maxLength}
        autoFocus
        autoComplete="off"
        aria-label={text.searchLabel}
        aria-autocomplete="list"
        aria-expanded={shown}
        aria-controls={listId}
        aria-activedescendant={current === undefined ? undefined : `${listId}-${active}`}
        placeholder={text.searchPlaceholder}
        onChange={(event) => {
          props.onChange(event.target.value);
          setOpen(true);
          setActive(-1);
        }}
        onClick={() => setOpen(true)}
        onBlur={close}
        onKeyDown={onKeyDown}
        className={`${FIELD} w-full`}
      />
      <ul
        id={listId}
        role="listbox"
        aria-label={text.suggestions}
        hidden={!shown}
        className="border-line-strong bg-panel absolute inset-x-0 top-full z-10 mt-1 max-h-[320px] overflow-y-auto rounded-xs border py-1 shadow-[0_8px_24px_rgb(0_0_0/0.7)]"
      >
        {suggestions.map((suggestion, index) => (
          <li
            key={suggestion}
            id={`${listId}-${index}`}
            role="option"
            aria-selected={index === active}
            // Le champ garde le focus : le clic n'est pas perdu à sa fermeture.
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => pick(suggestion)}
            className={`cursor-pointer truncate px-3 py-1.5 text-[16px] ${
              index === active ? "bg-field text-gold" : "text-ink hover:bg-field"
            }`}
          >
            {suggestion}
          </li>
        ))}
      </ul>
    </div>
  );
}
