"use client";

/**
 * Connexion Google du compte : rattacher, remplacer ou retirer.
 *
 * Un compte avec mot de passe le ressaisit. Google ne peut être retiré que s'il
 * reste un mot de passe pour se connecter.
 */
import { useState } from "react";

import type { LoginMethods } from "@/features/auth/api";
import { labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";
import { TextField } from "@/shared/ui/TextField";

import { startGoogleLink, unlinkGoogle } from "../accountApi";
import { useAccountAction } from "../useAccountAction";
import { FormHeading, FormStatus, SecondaryButton } from "./AccountFormParts";

interface GoogleFormProps {
  readonly methods: LoginMethods;
  readonly onSaved: () => void;
}

export function GoogleForm({ methods, onSaved }: GoogleFormProps) {
  const text = labels.profile.edit;
  const link = useAccountAction();
  const removal = useAccountAction();
  const [password, setPassword] = useState("");
  const [confirming, setConfirming] = useState(false);
  const busy = link.busy || removal.busy;
  const wrongPassword = [link, removal].some((action) => action.issue?.code === "wrong_password");

  function remove(): void {
    setConfirming(false);
    void removal.run(
      () => unlinkGoogle(password),
      () => {
        setPassword("");
        onSaved();
      },
    );
  }

  return (
    <section className="flex flex-col gap-4" aria-label={text.googleTitle}>
      <FormHeading>{text.googleTitle}</FormHeading>
      <p className="text-ink-muted text-[15px] italic">
        {methods.google ? text.googleLinkedHint : text.googleHint}
      </p>
      {methods.password && (
        <TextField
          label={text.currentPassword}
          name="google_current_password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
          invalid={wrongPassword}
          disabled={busy}
        />
      )}
      <FormStatus action={link} success={text.googleLeaving} />
      <FormStatus action={removal} success={text.googleRemoved} />
      <div className="flex flex-wrap gap-3">
        <SecondaryButton
          busy={busy}
          onClick={() =>
            void link.run(
              () => startGoogleLink(methods.password ? password : null),
              (url) => window.location.assign(url),
            )
          }
        >
          {methods.google ? text.googleReplace : text.googleLink}
        </SecondaryButton>
        {methods.google && methods.password && (
          <SecondaryButton busy={busy} onClick={() => setConfirming(true)}>
            {text.googleRemove}
          </SecondaryButton>
        )}
      </div>
      <ConfirmDialog
        open={confirming}
        title={text.googleRemoveTitle}
        question={text.googleRemoveQuestion}
        confirmLabel={text.googleRemove}
        cancelLabel={text.cancel}
        onConfirm={remove}
        onCancel={() => setConfirming(false)}
      />
    </section>
  );
}
