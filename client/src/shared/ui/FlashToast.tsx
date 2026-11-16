"use client";

/**
 * Notification en haut à droite ([Notification — Déconnexion réussie], 08c).
 * Elle disparaît seule après quelques secondes ou par son bouton de fermeture.
 */
import { useEffect, useSyncExternalStore } from "react";

import { labels } from "@/shared/i18n";

import { dismissFlash, readFlash, subscribeToFlash } from "./flash";

const AUTO_DISMISS_MS = 6000;

export function FlashToast() {
  const kind = useSyncExternalStore(subscribeToFlash, readFlash, () => null);

  useEffect(() => {
    if (kind === null) {
      return;
    }
    const timer = window.setTimeout(dismissFlash, AUTO_DISMISS_MS);
    return () => window.clearTimeout(timer);
  }, [kind]);

  if (kind === null) {
    return null;
  }
  const content = labels.flash[kind];

  return (
    <div
      role="status"
      className="border-gold animate-toast-in fixed top-8 right-8 z-50 flex w-[360px] items-start gap-3.5 rounded-md border bg-[rgb(22_16_13/0.95)] p-4 shadow-[0_12px_30px_rgb(0_0_0/0.8),0_0_18px_rgb(201_176_106/0.2)]"
    >
      <span
        aria-hidden="true"
        className="border-gold text-gold mt-1.5 flex size-[34px] shrink-0 items-center justify-center rounded-full border-[1.5px]"
      >
        <svg
          viewBox="0 0 16 16"
          className="size-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M3 8.5l3.2 3.2L13 4.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <div className="flex-1">
        <p className="font-display text-gold text-[10px] font-bold tracking-[2px]">
          {content.title}
        </p>
        <p className="text-ink mt-1 text-[15px] leading-tight font-medium">{content.message}</p>
      </div>
      <button
        type="button"
        onClick={dismissFlash}
        aria-label={labels.flash.close}
        className="text-ink-faint hover:text-ink cursor-pointer"
      >
        <svg viewBox="0 0 10 10" className="size-2.5" stroke="currentColor" strokeWidth="1.5">
          <path d="M1 1l8 8M9 1l-8 8" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}
