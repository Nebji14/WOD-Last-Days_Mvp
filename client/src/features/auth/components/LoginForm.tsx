"use client";

/**
 * Formulaire de connexion, pour les joueurs comme pour le MJ.
 *
 * Gère les identifiants incorrects, l'envoi en cours, la coupure réseau (les
 * valeurs saisies sont conservées) et le compte saisi sur la mauvaise page.
 */
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorLabel, labels } from "@/shared/i18n";
import { PrimaryButton } from "@/shared/ui/PrimaryButton";
import { TextField } from "@/shared/ui/TextField";

import { login } from "../api";
import {
  gmLoginPath,
  PLAYER_LOGIN_PATH,
  REGISTER_PATH,
  rememberGmBasePath,
  TABLE_PATH,
} from "../routes";
import { FooterLink, FormError, GoogleButton, OrSeparator } from "./FormParts";
import { WrongPortalMessage } from "./WrongPortalMessage";

type LoginFormProps =
  { readonly portal: "player" } | { readonly portal: "gm"; readonly gmBasePath: string };

const WRONG_PORTAL_CODES = ["wrong_portal_gm", "wrong_portal_player"];

/** Lien vers le bon accès, d'après l'erreur « mauvaise page » reçue. */
function wrongPortalHref(error: ApiError): string | null {
  if (error.code === "wrong_portal_player") {
    return PLAYER_LOGIN_PATH;
  }
  const gmBasePath = error.details.find((detail) => detail.gm_access_path)?.gm_access_path;
  return gmBasePath ? gmLoginPath(gmBasePath) : null;
}

export function LoginForm(props: LoginFormProps) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const isGm = props.portal === "gm";
  const text = labels.auth;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login({ username: username.trim(), password }, props.portal);
      if (props.portal === "gm") {
        rememberGmBasePath(props.gmBasePath);
      }
      router.replace(TABLE_PATH);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught : new ApiError(0, "internal_error"));
      setBusy(false);
    }
  }

  const isWrongPortal = error !== null && WRONG_PORTAL_CODES.includes(error.code);
  const invalidFields = error?.code === "invalid_credentials";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-[18px]" noValidate>
      <TextField
        label={isGm ? text.gm.usernameLabel : text.usernameLabel}
        name="username"
        value={username}
        onChange={setUsername}
        placeholder={isGm ? text.gm.usernamePlaceholder : text.login.usernamePlaceholder}
        autoComplete="username"
        invalid={invalidFields}
        disabled={busy}
        autoFocus
      />
      <TextField
        label={text.passwordLabel}
        name="password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
        invalid={invalidFields}
        disabled={busy}
      />

      {error !== null && isWrongPortal && (
        <WrongPortalMessage
          accountRole={error.code === "wrong_portal_gm" ? "gm" : "player"}
          href={wrongPortalHref(error)}
        />
      )}
      {error !== null && !isWrongPortal && <FormError message={errorLabel(error.code)} />}

      <PrimaryButton type="submit" busy={busy}>
        {text.login.submit}
      </PrimaryButton>
      <OrSeparator />
      <GoogleButton label={text.login.google} />

      {isGm ? (
        <p className="text-ink-muted pt-1.5 text-center text-[17px] leading-[21px] font-medium">
          {text.gm.restricted}
        </p>
      ) : (
        <FooterLink
          prompt={text.login.noAccount}
          label={text.login.toRegister}
          href={REGISTER_PATH}
        />
      )}
    </form>
  );
}
