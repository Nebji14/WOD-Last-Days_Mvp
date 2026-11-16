"use client";

/**
 * [Saisie — message] : Entrée ou « ENVOYER » envoie le message (03-I6).
 *
 * Le champ est vidé dès l'envoi : le message part en attente et n'a jamais à
 * être ressaisi, même si la connexion est coupée (03-E7).
 */
import { type FormEvent, useState } from "react";

import { labels } from "@/shared/i18n";

import { MESSAGE_MAX_LENGTH } from "../api";

interface ChatComposerProps {
  readonly onSend: (body: string) => void;
  /** Classes de dimension du champ : état replié ou déroulé. */
  readonly className: string;
}

export function ChatComposer({ onSend, className }: ChatComposerProps) {
  const [draft, setDraft] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const body = draft.trim();
    if (body === "") {
      return;
    }
    onSend(body);
    setDraft("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`border-line bg-panel focus-within:border-gold flex shrink-0 items-center rounded-xs border ${className}`}
    >
      <input
        type="text"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        maxLength={MESSAGE_MAX_LENGTH}
        aria-label={labels.chat.inputLabel}
        placeholder={labels.chat.placeholder}
        autoComplete="off"
        className="text-ink placeholder:text-ink-faint h-full min-w-0 flex-1 bg-transparent pl-2.5 text-[15px] font-medium outline-none placeholder:italic"
      />
      <button
        type="submit"
        className="font-display text-copper hover:text-copper-light cursor-pointer px-2.5 text-[10px] font-bold tracking-[2px]"
      >
        {labels.chat.send}
      </button>
    </form>
  );
}
