"use client";

/** Éléments partagés par les formulaires du compte. */
import type { ReactNode } from "react";

import { IssueMessage } from "@/features/auth/components/FormParts";
import { labels } from "@/shared/i18n";

import { startGoogleConfirmation } from "../accountApi";
import { type AccountAction, useAccountAction } from "../useAccountAction";

interface SecondaryButtonProps {
  readonly children: ReactNode;
  readonly busy?: boolean;
  readonly onClick: () => void;
}

export function SecondaryButton({ children, busy = false, onClick }: SecondaryButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy}
      aria-busy={busy}
      className="border-line-strong font-display text-ink min-h-11 cursor-pointer rounded-xs border px-4 py-2 text-[11px] font-bold tracking-[2px] hover:brightness-125 disabled:cursor-wait disabled:opacity-60"
    >
      {children}
    </button>
  );
}

/** Titre d'une partie du compte. */
export function FormHeading({ children }: { readonly children: ReactNode }) {
  return (
    <h3 className="font-display text-gold text-[11px] font-bold tracking-[3px]">{children}</h3>
  );
}

interface FormStatusProps {
  readonly action: AccountAction;
  readonly success: string;
}

/**
 * Résultat du dernier envoi. Un compte sans mot de passe dont la connexion est
 * ancienne est invité à se reconnecter avec Google.
 */
export function FormStatus({ action, success }: FormStatusProps) {
  const confirmation = useAccountAction();
  const { issue } = action;

  if (issue === null) {
    return action.done ? (
      <p role="status" className="text-valid text-[17px] italic">
        ✓ {success}
      </p>
    ) : null;
  }
  return (
    <>
      <IssueMessage issue={issue} />
      {issue.code === "reauthentication_required" && (
        <SecondaryButton
          busy={confirmation.busy}
          onClick={() =>
            void confirmation.run(startGoogleConfirmation, (url) => window.location.assign(url))
          }
        >
          {labels.profile.edit.confirmWithGoogle}
        </SecondaryButton>
      )}
      {confirmation.issue !== null && <IssueMessage issue={confirmation.issue} />}
    </>
  );
}
