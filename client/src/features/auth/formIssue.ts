/** Refus d'un formulaire de compte : code à traduire et règles de mot de passe en cause. */
import { ApiError } from "@/shared/api/client";

import { isPasswordRule, type PasswordRule, passwordViolations } from "./validation";

export interface FormIssue {
  readonly code: string;
  readonly rules: readonly PasswordRule[];
}

/** Convertit une erreur de l'API en refus affichable. */
export function toIssue(error: unknown): FormIssue {
  if (!(error instanceof ApiError)) {
    return { code: "internal_error", rules: [] };
  }
  return {
    code: error.code,
    rules: error.details.map((detail) => detail.rule).filter(isPasswordRule),
  };
}

/** Contrôle un nouveau mot de passe avant l'envoi ; `null` s'il est acceptable. */
export function findPasswordIssue(password: string, confirmation: string): FormIssue | null {
  const rules = passwordViolations(password);
  if (rules.length > 0) {
    return { code: "password_too_weak", rules };
  }
  return password === confirmation ? null : { code: "password_mismatch", rules: [] };
}
