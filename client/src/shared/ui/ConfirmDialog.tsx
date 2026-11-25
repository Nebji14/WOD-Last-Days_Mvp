"use client";

/**
 * Fenêtre de confirmation, utilisée avant toute suppression.
 *
 * Repose sur l'élément natif `<dialog>` : le reste de la page devient inerte, le
 * focus reste dans la fenêtre, Échap ou un clic sur le fond annulent.
 */
import { useEffect, useId, useRef } from "react";

interface ConfirmDialogProps {
  readonly open: boolean;
  /** Titre en capitales (Cinzel). */
  readonly title: string;
  /** Question posée, en texte courant. */
  readonly question: string;
  readonly confirmLabel: string;
  readonly cancelLabel: string;
  readonly onConfirm: () => void;
  readonly onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  question,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (dialog === null) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onClick={(event) => event.target === event.currentTarget && onCancel()}
      className="bg-panel border-line-strong text-ink m-auto w-[380px] max-w-[calc(100vw-32px)] rounded-xs border p-0 shadow-[0_0_40px_rgb(0_0_0/0.8)] backdrop:bg-black/70"
    >
      <div className="flex flex-col gap-5 px-7 py-6">
        <h2
          id={titleId}
          className="font-display text-copper-light text-[13px] font-bold tracking-[3px]"
        >
          {title}
        </h2>
        <p className="font-body text-ink text-lg">{question}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            autoFocus
            onClick={onCancel}
            className="border-line-strong font-display text-ink-muted hover:text-ink cursor-pointer rounded-xs border px-4 py-2 text-[11px] font-bold tracking-[2px]"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright cursor-pointer rounded-xs border bg-linear-to-b px-4 py-2 text-[11px] font-bold tracking-[2px] shadow-[0_0_12px_rgb(216_53_44/0.33)] hover:brightness-110"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
