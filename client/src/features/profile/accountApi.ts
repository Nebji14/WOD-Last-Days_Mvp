/** Appels API de modification de son propre compte. */
import { type Account, parseAccount } from "@/features/auth/api";
import { keepOriginal, type PortraitFiles, uploadPortrait } from "@/features/characters/portrait";
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

export interface AccountNames {
  readonly username: string;
  readonly displayName: string;
}

export interface NewPassword {
  /** `null` pour un compte qui n'a pas encore de mot de passe. */
  readonly current: string | null;
  readonly password: string;
  readonly confirmation: string;
}

function parseGoogleUrl(data: unknown): string {
  if (isRecord(data) && typeof data.url === "string") {
    return data.url;
  }
  throw new ApiError(502, "internal_error");
}

/** Modifie le nom d'utilisateur et le nom affiché. */
export function updateNames(names: AccountNames): Promise<Account> {
  return apiRequest("/api/account", {
    method: "PATCH",
    body: { username: names.username, display_name: names.displayName },
    parse: parseAccount,
  });
}

/** Départ d'un joueur : désactiver son compte, ou le supprimer définitivement. */
export type Closure = "disable" | "delete";

/**
 * Ferme le compte du joueur.
 *
 * @param username nom d'utilisateur recopié à l'identique.
 * @param currentPassword `null` pour un compte sans mot de passe.
 */
export function closeAccount(
  closure: Closure,
  username: string,
  currentPassword: string | null,
): Promise<void> {
  return apiRequest(`/api/account/${closure}`, {
    method: "POST",
    body: { username, current_password: currentPassword },
  });
}

/** Donne une photo au MJ, à la place de la précédente. */
export async function setAccountPortrait(files: PortraitFiles): Promise<void> {
  const account = await uploadPortrait("/api/account/portrait", files.portrait, parseAccount);
  await keepOriginal(account.portrait, files.original);
}

/** Retire la photo du MJ. */
export function removeAccountPortrait(): Promise<void> {
  return apiRequest("/api/account/portrait", { method: "DELETE" });
}

/** Change le mot de passe, ou définit le premier. Les autres sessions sont fermées. */
export function changePassword(change: NewPassword): Promise<void> {
  return apiRequest("/api/account/password", {
    method: "POST",
    body: {
      current_password: change.current,
      password: change.password,
      password_confirmation: change.confirmation,
    },
  });
}

/** Adresse de Google où aller rattacher un compte, ou remplacer l'actuel. */
export function startGoogleLink(currentPassword: string | null): Promise<string> {
  return apiRequest("/api/account/google/link", {
    method: "POST",
    body: { current_password: currentPassword },
    parse: parseGoogleUrl,
  });
}

/** Adresse de Google où se reconnecter pour confirmer son identité. */
export function startGoogleConfirmation(): Promise<string> {
  return apiRequest("/api/account/google/confirm", { method: "POST", parse: parseGoogleUrl });
}

/** Retire la connexion Google. Le compte garde son mot de passe. */
export function unlinkGoogle(currentPassword: string): Promise<void> {
  return apiRequest("/api/account/google/unlink", {
    method: "POST",
    body: { current_password: currentPassword },
  });
}
