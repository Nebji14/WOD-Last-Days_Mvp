"use client";

/** Modification du nom affiché et du nom d'utilisateur. */
import { type FormEvent, useState } from "react";

import type { Account } from "@/features/auth/api";
import { isValidUsername, normalizedDisplayName } from "@/features/auth/validation";
import { labels } from "@/shared/i18n";
import { PrimaryButton } from "@/shared/ui/PrimaryButton";
import { TextField } from "@/shared/ui/TextField";

import { updateNames } from "../accountApi";
import { useAccountAction } from "../useAccountAction";
import { FormHeading, FormStatus } from "./AccountFormParts";

interface NamesFormProps {
  readonly account: Account;
  readonly onSaved: () => void;
}

export function NamesForm({ account, onSaved }: NamesFormProps) {
  const text = labels.profile;
  const action = useAccountAction();
  const [displayName, setDisplayName] = useState(account.displayName);
  const [username, setUsername] = useState(account.username);
  const code = action.issue?.code ?? "";

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const name = normalizedDisplayName(displayName);
    const login = username.trim();
    if (name === null) {
      action.refuse({ code: "display_name_invalid", rules: [] });
    } else if (!isValidUsername(login)) {
      action.refuse({ code: "username_invalid", rules: [] });
    } else {
      void action.run(
        () => updateNames({ username: login, displayName: name }),
        (saved) => {
          setDisplayName(saved.displayName);
          setUsername(saved.username);
          onSaved();
        },
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <FormHeading>{text.edit.namesTitle}</FormHeading>
      <TextField
        label={text.account.displayName}
        name="display_name"
        value={displayName}
        onChange={setDisplayName}
        autoComplete="nickname"
        invalid={code.startsWith("display_name")}
        disabled={action.busy}
      />
      <TextField
        label={text.account.username}
        name="username"
        value={username}
        onChange={setUsername}
        autoComplete="username"
        invalid={code.startsWith("username")}
        disabled={action.busy}
      />
      <p className="text-ink-muted text-[15px] italic">{text.edit.namesHint}</p>
      <FormStatus action={action} success={text.edit.namesSaved} />
      <PrimaryButton type="submit" busy={action.busy}>
        {text.edit.save}
      </PrimaryButton>
    </form>
  );
}
