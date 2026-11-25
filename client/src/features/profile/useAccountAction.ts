"use client";

/** Envoi d'un formulaire de compte : état d'attente, refus et confirmation. */
import { useState } from "react";

import { type FormIssue, toIssue } from "@/features/auth/formIssue";

export interface AccountAction {
  readonly busy: boolean;
  readonly issue: FormIssue | null;
  /** Le dernier envoi a réussi. */
  readonly done: boolean;
  readonly refuse: (issue: FormIssue) => void;
  /** Lance l'action ; `onSuccess` reçoit son résultat. */
  readonly run: <T>(action: () => Promise<T>, onSuccess: (result: T) => void) => Promise<void>;
}

export function useAccountAction(): AccountAction {
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<FormIssue | null>(null);
  const [done, setDone] = useState(false);

  function refuse(next: FormIssue): void {
    setDone(false);
    setIssue(next);
  }

  async function run<T>(action: () => Promise<T>, onSuccess: (result: T) => void): Promise<void> {
    setBusy(true);
    setIssue(null);
    setDone(false);
    try {
      const result = await action();
      setDone(true);
      onSuccess(result);
    } catch (error) {
      setIssue(toIssue(error));
    } finally {
      setBusy(false);
    }
  }

  return { busy, issue, done, refuse, run };
}
