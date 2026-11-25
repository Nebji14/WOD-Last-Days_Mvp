"use client";

/** Changement du mot de passe, ou premier mot de passe d'un compte Google. */
import { type FormEvent, useState } from "react";

import { findPasswordIssue } from "@/features/auth/formIssue";
import { labels } from "@/shared/i18n";
import { PrimaryButton } from "@/shared/ui/PrimaryButton";
import { TextField } from "@/shared/ui/TextField";

import { changePassword } from "../accountApi";
import { useAccountAction } from "../useAccountAction";
import { FormHeading, FormStatus } from "./AccountFormParts";

interface PasswordFormProps {
  readonly hasPassword: boolean;
  readonly onSaved: () => void;
}

export function PasswordForm({ hasPassword, onSaved }: PasswordFormProps) {
  const text = labels.profile.edit;
  const action = useAccountAction();
  const [current, setCurrent] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const code = action.issue?.code;

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const issue = findPasswordIssue(password, confirmation);
    if (issue !== null) {
      action.refuse(issue);
      return;
    }
    void action.run(
      () => changePassword({ current: hasPassword ? current : null, password, confirmation }),
      () => {
        setCurrent("");
        setPassword("");
        setConfirmation("");
        onSaved();
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <FormHeading>{hasPassword ? text.passwordTitle : text.firstPasswordTitle}</FormHeading>
      {hasPassword && (
        <TextField
          label={text.currentPassword}
          name="current_password"
          type="password"
          value={current}
          onChange={setCurrent}
          autoComplete="current-password"
          invalid={code === "wrong_password"}
          disabled={action.busy}
        />
      )}
      <TextField
        label={text.newPassword}
        name="new_password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        invalid={code === "password_too_weak"}
        disabled={action.busy}
      />
      <TextField
        label={labels.auth.passwordConfirmationLabel}
        name="new_password_confirmation"
        type="password"
        value={confirmation}
        onChange={setConfirmation}
        autoComplete="new-password"
        invalid={code === "password_mismatch"}
        disabled={action.busy}
      />
      <p className="text-ink-muted text-[15px] italic">
        {hasPassword ? text.passwordHint : text.firstPasswordHint}
      </p>
      <FormStatus action={action} success={text.passwordSaved} />
      <PrimaryButton type="submit" busy={action.busy}>
        {text.save}
      </PrimaryButton>
    </form>
  );
}
