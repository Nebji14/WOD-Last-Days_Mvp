/**
 * Bouton d'action principale : rouge, réservé aux actions importantes (légende T5).
 * Pendant un envoi, il est désactivé et affiche un indicateur (02a-E3).
 */
import type { ReactNode } from "react";

interface PrimaryButtonProps {
  readonly children: ReactNode;
  readonly type?: "button" | "submit";
  readonly busy?: boolean;
  readonly onClick?: () => void;
}

export function PrimaryButton({
  children,
  type = "button",
  busy = false,
  onClick,
}: PrimaryButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={busy}
      aria-busy={busy}
      className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright flex h-[52px] w-full cursor-pointer items-center justify-center gap-3 rounded-xs border bg-linear-to-b text-[17px] font-bold tracking-[3px] shadow-[0_0_16px_rgb(216_53_44/0.33)] transition hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
    >
      {busy && (
        <span
          aria-hidden="true"
          className="border-ink-bright/40 border-t-ink-bright size-4 animate-spin rounded-full border-2"
        />
      )}
      {children}
    </button>
  );
}
