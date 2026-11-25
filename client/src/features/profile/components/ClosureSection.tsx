"use client";

/** « Quitter la campagne » : un joueur désactive son compte, ou le supprime définitivement. */
import { useState } from "react";

import type { Account, LoginMethods } from "@/features/auth/api";
import { PLAYER_LOGIN_PATH } from "@/features/auth/routes";
import { labels } from "@/shared/i18n";

import type { Closure } from "../accountApi";
import { FormHeading, SecondaryButton } from "./AccountFormParts";
import { ClosureDialog } from "./ClosureDialog";

interface ClosureSectionProps {
  readonly account: Account;
  readonly methods: LoginMethods;
}

/** Quitte le profil : sa fenêtre se ferme, ou revient à la connexion si elle est seule. */
function leave(): void {
  if (window.opener === null) {
    window.location.assign(PLAYER_LOGIN_PATH);
  } else {
    window.close();
  }
}

export function ClosureSection({ account, methods }: ClosureSectionProps) {
  const text = labels.profile.closure;
  const [closure, setClosure] = useState<Closure | null>(null);

  return (
    <section
      aria-label={text.heading}
      className="border-line-soft flex flex-col gap-4 border-t pt-7"
    >
      <FormHeading>{text.heading}</FormHeading>
      <p className="text-ink-muted text-[15px] italic">{text.disable.hint}</p>
      <SecondaryButton onClick={() => setClosure("disable")}>{text.disable.open}</SecondaryButton>
      <p className="text-ink-muted text-[15px] italic">{text.delete.hint}</p>
      <button
        type="button"
        onClick={() => setClosure("delete")}
        className="border-danger font-display text-danger min-h-11 cursor-pointer rounded-xs border px-4 py-2 text-[11px] font-bold tracking-[2px] hover:brightness-125"
      >
        {text.delete.open}
      </button>
      {closure !== null && (
        <ClosureDialog
          closure={closure}
          account={account}
          methods={methods}
          onClose={() => setClosure(null)}
          onLeft={leave}
        />
      )}
    </section>
  );
}
