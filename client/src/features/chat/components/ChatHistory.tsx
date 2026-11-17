"use client";

/**
 * Historique du chat déroulé.
 *
 * - À l'ouverture, l'affichage est calé sur les messages les plus récents et y
 *   reste tant que le lecteur ne remonte pas.
 * - Remonter en haut charge les messages plus anciens sans déplacer la lecture.
 * - Dès que le lecteur a remonté, un bouton ramène aux plus récents.
 */
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { errorLabel, labels } from "@/shared/i18n";

import type { ChatMessage } from "../api";
import { type PendingMessage, useChatStore } from "../store";
import { buildTimeline } from "../timeline";
import { MessageRow } from "./MessageRow";

interface ChatHistoryProps {
  readonly messages: readonly ChatMessage[];
  readonly pending: readonly PendingMessage[];
  readonly viewerId: string;
  readonly viewerIsGm: boolean;
}

const BOTTOM_THRESHOLD_PX = 24;
const TOP_THRESHOLD_PX = 60;

function PendingRow({ item }: { readonly item: PendingMessage }) {
  const text = labels.chat;
  return (
    <div className="text-ink-muted text-[15px] leading-[19px] font-medium break-words">
      <p>{item.body}</p>
      {item.errorCode === null ? (
        <p className="text-ink-faint text-sm italic">{text.sending}</p>
      ) : (
        <p className="text-danger flex items-center gap-3 text-sm">
          <span>
            {text.notSent} — {errorLabel(item.errorCode)}
          </span>
          <button
            type="button"
            onClick={() => useChatStore.getState().discardPending(item.clientToken)}
            className="font-display text-ink-muted cursor-pointer text-[9px] font-bold tracking-[1.5px]"
          >
            {text.discard}
          </button>
        </p>
      )}
    </div>
  );
}

export function ChatHistory({ messages, pending, viewerId, viewerIsGm }: ChatHistoryProps) {
  const text = labels.chat;
  const hasMore = useChatStore((state) => state.hasMore);
  const loadingOlder = useChatStore((state) => state.loadingOlder);
  const scrollRef = useRef<HTMLDivElement>(null);
  /** Le lecteur est en bas de l'historique : les nouveaux messages le font défiler. */
  const followRef = useRef(true);
  /** Hauteur du contenu avant le chargement d'une page plus ancienne. */
  const heightBeforeOlderRef = useRef<number | null>(null);
  const [atBottom, setAtBottom] = useState(true);
  const [now] = useState(() => new Date());

  useLayoutEffect(() => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    if (heightBeforeOlderRef.current !== null && !loadingOlder) {
      element.scrollTop += element.scrollHeight - heightBeforeOlderRef.current;
      heightBeforeOlderRef.current = null;
    } else if (followRef.current) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages, pending, loadingOlder]);

  // Pendant le déroulé du panneau, la hauteur change : la lecture reste calée en bas.
  useEffect(() => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver(() => {
      if (followRef.current) {
        element.scrollTop = element.scrollHeight;
      }
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  function handleScroll(): void {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    followRef.current = distance < BOTTOM_THRESHOLD_PX;
    setAtBottom(followRef.current);
    if (element.scrollTop < TOP_THRESHOLD_PX && hasMore && !loadingOlder) {
      heightBeforeOlderRef.current = element.scrollHeight;
      void useChatStore
        .getState()
        .loadOlder()
        .catch(() => undefined);
    }
  }

  function backToLatest(): void {
    const element = scrollRef.current;
    if (element) {
      followRef.current = true;
      element.scrollTop = element.scrollHeight;
      setAtBottom(true);
    }
  }

  return (
    <div className="animate-chat-content relative min-h-0 flex-1">
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        tabIndex={0}
        role="log"
        aria-label={text.title}
        className="flex h-full flex-col gap-[9px] overflow-y-auto px-4 py-3 [scrollbar-color:var(--color-line)_transparent] [scrollbar-width:thin]"
      >
        <p className="text-ink-faint mt-auto text-sm leading-[17px] font-medium italic">
          {loadingOlder ? text.loadingOlder : hasMore ? text.scrollHint : ""}
        </p>
        {messages.length === 0 && pending.length === 0 && (
          <p className="text-ink-faint text-[15px] italic">{text.empty}</p>
        )}
        {buildTimeline(messages, now).map((item) =>
          item.kind === "day" ? (
            <p
              key={item.key}
              className="font-display text-ink-faint text-center text-[8px] leading-[11px] font-bold tracking-[2px]"
            >
              — {item.label} —
            </p>
          ) : (
            <MessageRow
              key={item.key}
              message={item.message}
              canModerate={viewerIsGm || item.message.author.id === viewerId}
              interactive
            />
          ),
        )}
        {pending.map((item) => (
          <PendingRow key={item.clientToken} item={item} />
        ))}
      </div>
      {!atBottom && (
        <button
          type="button"
          onClick={backToLatest}
          className="border-gold/60 text-gold absolute bottom-2 left-1/2 -translate-x-1/2 cursor-pointer rounded-full border bg-[#1e1813] px-3.5 py-1 text-sm font-medium italic shadow-[0_4px_12px_rgb(0_0_0/0.6)]"
        >
          {text.backToLatest}
        </button>
      )}
    </div>
  );
}
