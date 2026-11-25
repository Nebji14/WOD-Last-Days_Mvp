"use client";

/**
 * Panneau « Mon compte » du profil : informations et méthodes de connexion, ou
 * leur modification. Chaque partie s'enregistre séparément.
 */
import { useState } from "react";

import type { Account } from "@/features/auth/api";
import { initials } from "@/features/table/seatLayout";
import { errorLabel, labels } from "@/shared/i18n";

import type { GoogleResult } from "../googleResult";
import { useLoginMethods } from "../useLoginMethods";
import { AccountSummary } from "./AccountSummary";
import { GoogleForm } from "./GoogleForm";
import { NamesForm } from "./NamesForm";
import { PasswordForm } from "./PasswordForm";

interface AccountPanelProps {
  readonly account: Account;
  /** Résultat à afficher au retour de Google, `null` sinon. */
  readonly googleResult: GoogleResult | null;
  readonly onChanged: () => void;
}

/** Message affiché au retour de Google. */
function GoogleNotice({ result }: { readonly result: GoogleResult }) {
  const text = labels.profile.edit;
  if (result.kind === "error") {
    return (
      <p role="alert" className="text-danger mt-5 text-center text-[17px] font-semibold">
        {errorLabel(result.code)}
      </p>
    );
  }
  return (
    <p role="status" className="text-valid mt-5 text-center text-[17px] italic">
      ✓ {result.kind === "linked" ? text.googleLinked : text.googleConfirmed}
    </p>
  );
}

export function AccountPanel({ account, googleResult, onChanged }: AccountPanelProps) {
  const text = labels.profile;
  const isGm = account.role === "gm";
  const { methods, refresh } = useLoginMethods();
  // Après une confirmation par Google, la modification en cours reprend.
  const [editing, setEditing] = useState(googleResult?.kind === "confirmed");

  return (
    <section
      aria-label={text.account.title}
      className="border-line bg-panel flex flex-col rounded-xs border px-6 py-8 lg:min-h-0 lg:overflow-y-auto"
    >
      <div className="border-line-soft flex flex-col items-center gap-2 border-b pb-6">
        <span
          aria-hidden="true"
          className="border-gold bg-field font-display text-gold flex size-28 items-center justify-center rounded-full border-2 text-5xl font-bold shadow-[0_0_24px_rgb(201_176_106/0.2)]"
        >
          {isGm ? labels.table.gm.initials : initials(account.displayName).slice(0, 1)}
        </span>
        <h2 className="text-ink-bright mt-3 max-w-full text-center text-3xl font-bold break-words">
          {account.displayName}
        </h2>
        <p className="text-ink-muted flex items-center gap-2 italic">
          <span aria-hidden="true" className="bg-online size-2.5 rounded-full" />
          {isGm ? text.status.gm : text.status.player}
        </p>
      </div>

      {googleResult !== null && <GoogleNotice result={googleResult} />}

      {editing ? (
        <div className="mt-6 mb-7 flex flex-col gap-9">
          <NamesForm account={account} onSaved={onChanged} />
          {methods !== null && (
            <>
              <PasswordForm hasPassword={methods.password} onSaved={refresh} />
              <GoogleForm methods={methods} onSaved={refresh} />
            </>
          )}
        </div>
      ) : (
        <div className="mb-7">
          <AccountSummary account={account} methods={methods} />
        </div>
      )}

      <button
        type="button"
        onClick={() => setEditing(!editing)}
        className="border-line-strong font-display text-ink mt-auto min-h-11 shrink-0 cursor-pointer rounded-xs border text-[11px] font-bold tracking-[2.5px] hover:brightness-125"
      >
        {editing ? text.edit.close : text.editInfo}
      </button>
    </section>
  );
}
