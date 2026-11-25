"use client";

/**
 * Formulaire d'inscription d'un joueur.
 *
 * Contrôles V1 à V3 : nom déjà pris, confirmation différente, mot de passe non
 * conforme. Après un succès, le joueur est renvoyé vers la connexion sans être
 * connecté.
 */
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { labels } from "@/shared/i18n";
import { setFlashForNextPage } from "@/shared/ui/flash";
import { PrimaryButton } from "@/shared/ui/PrimaryButton";
import { TextField } from "@/shared/ui/TextField";

import { googleStartUrl, register } from "../api";
import { findPasswordIssue, type FormIssue, toIssue } from "../formIssue";
import { PLAYER_LOGIN_PATH } from "../routes";
import { isValidUsername } from "../validation";
import { FooterLink, GoogleButton, IssueMessage, OrSeparator } from "./FormParts";

/** Contrôle la saisie avant l'envoi, dans l'ordre d'affichage des champs. */
function findLocalIssue(
  username: string,
  password: string,
  confirmation: string,
): FormIssue | null {
  if (!isValidUsername(username)) {
    return { code: "username_invalid", rules: [] };
  }
  return findPasswordIssue(password, confirmation);
}

export function RegisterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<FormIssue | null>(null);
  const text = labels.auth;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const trimmedUsername = username.trim();
    const localIssue = findLocalIssue(trimmedUsername, password, confirmation);
    if (localIssue !== null) {
      setIssue(localIssue);
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await register({ username: trimmedUsername, password }, confirmation);
      setFlashForNextPage("registered");
      router.push(PLAYER_LOGIN_PATH);
    } catch (caught) {
      setIssue(toIssue(caught));
      setBusy(false);
    }
  }

  const usernameInvalid = issue?.code === "username_invalid" || issue?.code === "username_taken";
  const passwordInvalid = issue?.code === "password_too_weak";
  const confirmationInvalid = issue?.code === "password_mismatch";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-[18px]" noValidate>
      <TextField
        label={text.usernameLabel}
        name="username"
        value={username}
        onChange={setUsername}
        placeholder={text.register.usernamePlaceholder}
        autoComplete="username"
        invalid={usernameInvalid}
        disabled={busy}
        autoFocus
      />
      <TextField
        label={text.passwordLabel}
        name="password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        invalid={passwordInvalid}
        disabled={busy}
      />
      <TextField
        label={text.passwordConfirmationLabel}
        name="password_confirmation"
        type="password"
        value={confirmation}
        onChange={setConfirmation}
        autoComplete="new-password"
        invalid={confirmationInvalid}
        disabled={busy}
      />

      {issue !== null && <IssueMessage issue={issue} />}

      <PrimaryButton type="submit" busy={busy}>
        {text.register.submit}
      </PrimaryButton>
      <OrSeparator />
      <GoogleButton label={text.register.google} href={googleStartUrl("player")} />
      <FooterLink
        prompt={text.register.hasAccount}
        label={text.register.toLogin}
        href={PLAYER_LOGIN_PATH}
      />
    </form>
  );
}
