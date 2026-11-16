"use client";

/**
 * Chat général de la table (US-013, US-029, US-030).
 *
 * - [Chat (replié)] : en bas à droite, toujours visible, avec les derniers
 *   messages et la saisie (03).
 * - [Chat (déroulé)] : le panneau s'agrandit vers le haut et montre tout
 *   l'historique, avec les actions sur les messages (03-A4, 03-E6, 08b).
 */
import { useState } from "react";

import { labels } from "@/shared/i18n";

import { useChatStore } from "../store";
import { ChatComposer } from "./ChatComposer";
import { ChatHistory } from "./ChatHistory";
import { MessageRow } from "./MessageRow";

interface ChatPanelProps {
  readonly viewerId: string;
  readonly viewerIsGm: boolean;
}

/** Nombre de messages gardés dans l'aperçu replié ; le cadre masque ceux qui dépassent. */
const PREVIEW_COUNT = 6;

export function ChatPanel({ viewerId, viewerIsGm }: ChatPanelProps) {
  const text = labels.chat;
  const [expanded, setExpanded] = useState(false);
  const messages = useChatStore((state) => state.messages);
  const pending = useChatStore((state) => state.pending);
  const send = useChatStore((state) => state.send);

  return (
    <section
      aria-label={text.title}
      className={`border-line absolute z-20 flex flex-col rounded-md border ${
        expanded
          ? "animate-chat-unfold top-[112px] right-4 bottom-3.5 w-[384px] bg-[rgb(14_11_10/0.98)] shadow-[0_16px_40px_rgb(0_0_0/0.87)]"
          : "right-5 bottom-4 h-[212px] w-[290px] bg-[rgb(14_11_10/0.96)] shadow-[0_10px_24px_rgb(0_0_0/0.67)]"
      }`}
    >
      <header
        className={`border-line-soft flex shrink-0 items-center justify-between border-b ${
          expanded ? "h-[38px] pr-3.5 pl-4" : "h-[34px] pr-2.5 pl-3.5"
        }`}
      >
        <h2 className="font-display text-gold text-[11px] font-bold tracking-[3px]">
          {text.title}
        </h2>
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          aria-expanded={expanded}
          className="font-display text-ink-muted hover:text-ink flex cursor-pointer items-center gap-1.5 text-[9px] font-bold tracking-[2px]"
        >
          {expanded ? text.collapse : text.expand}
          <svg
            viewBox="0 0 10 6"
            aria-hidden="true"
            className={`h-1.5 w-2.5 ${expanded ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M1 5l4-4 4 4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </header>

      {expanded ? (
        <ChatHistory
          messages={messages}
          pending={pending}
          viewerId={viewerId}
          viewerIsGm={viewerIsGm}
        />
      ) : (
        <div className="flex min-h-0 flex-1 flex-col justify-end gap-[5px] overflow-hidden px-3.5 pt-2 pb-2.5">
          {messages.slice(-PREVIEW_COUNT).map((message) => (
            <MessageRow
              key={message.id}
              message={message}
              canModerate={false}
              interactive={false}
            />
          ))}
          {pending.map((item) => (
            <p key={item.clientToken} className="text-ink-muted text-[15px] leading-[18px] italic">
              {item.body}
            </p>
          ))}
        </div>
      )}

      <ChatComposer
        onSend={send}
        className={expanded ? "mx-3 mb-3 h-9" : "mx-2.5 mb-2.5 h-[34px]"}
      />
    </section>
  );
}
