/**
 * Reflet côté client des règles de compte, pour signaler une erreur avant
 * l'envoi. Le serveur reste seul garant (server/app/domain/accounts.py).
 */
export type PasswordRule = "min_length" | "max_length" | "letter" | "digit";

const USERNAME_PATTERN = /^[A-Za-z0-9._-]{3,24}$/;
const DISPLAY_NAME_MAX_LENGTH = 40;
const PASSWORD_MIN_LENGTH = 10;
const PASSWORD_MAX_BYTES = 72;

export function isValidUsername(username: string): boolean {
  return USERNAME_PATTERN.test(username);
}

/** Nom affiché sans espace superflu, ou `null` s'il n'est pas valide. */
export function normalizedDisplayName(name: string): string | null {
  const normalized = name.normalize("NFC").trim().replace(/\s+/g, " ");
  const length = [...normalized].length;
  if (length < 1 || length > DISPLAY_NAME_MAX_LENGTH || /\p{C}/u.test(normalized)) {
    return null;
  }
  return normalized;
}

/** Liste les règles de sécurité non respectées par un mot de passe. */
export function passwordViolations(password: string): PasswordRule[] {
  const violations: PasswordRule[] = [];
  if (password.length < PASSWORD_MIN_LENGTH) {
    violations.push("min_length");
  }
  if (new TextEncoder().encode(password).length > PASSWORD_MAX_BYTES) {
    violations.push("max_length");
  }
  if (!/\p{L}/u.test(password)) {
    violations.push("letter");
  }
  if (!/\p{Nd}/u.test(password)) {
    violations.push("digit");
  }
  return violations;
}

export function isPasswordRule(value: string | undefined): value is PasswordRule {
  return (
    value === "min_length" || value === "max_length" || value === "letter" || value === "digit"
  );
}
