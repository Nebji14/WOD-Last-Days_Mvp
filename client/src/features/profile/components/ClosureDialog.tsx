"use client";

/**
 * Confirmation du départ d'un joueur : désactiver ou supprimer son compte.
 *
 * Le bouton reste bloqué tant que le nom d'utilisateur n'est pas recopié à
 * l'identique, et le mot de passe saisi s'il y en a un.
 */
import { type FormEvent, useEffect, useId, useRef, useState } from "react";

import type { Account, LoginMethods } from "@/features/auth/api";
import { fill, labels } from "@/shared/i18n";
import { TextField } from "@/shared/ui/TextField";

import { type Closure, closeAccount } from "../accountApi";
import { useAccountAction } from "../useAccountAction";
import { FormStatus } from "./AccountFormParts";

interface ClosureDialogProps {
  readonly closure: Closure;
  readonly account: Account;
  readonly methods: LoginMethods;
  readonly onClose: () => void;
  readonly onLeft: () => void;
}

export function ClosureDialog(props: ClosureDialogProps) {
  const { closure, account, methods, onClose, onLeft } = props;
  const text = labels.profile.closure;
  const wording = text[closure];
  const action = useAccountAction();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const ready = username === account.username && (!methods.password || password !== "");
  const code = action.issue?.code;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog !== null && !dialog.open) {
      dialog.showModal();
    }
  }, []);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (ready) {
      void action.run(
        () => closeAccount(closure, username, methods.password ? password : null),
        onLeft,
      );
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!action.busy) onClose();
      }}
      className="bg-panel border-danger text-ink m-auto w-[460px] max-w-[calc(100vw-32px)] rounded-xs border p-0 shadow-[0_0_40px_rgb(0_0_0/0.8)] backdrop:bg-black/75"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 px-6 py-6" noValidate>
        <h2
          id={titleId}
          className="font-display text-danger-bright text-[13px] font-bold tracking-[3px]"
        >
          {wording.title}
        </h2>
        <p className="text-lg">{wording.question}</p>
        <ul className="text-ink-muted list-inside list-disc text-[17px]">
          {wording.effects.map((effect) => (
            <li key={effect}>{effect}</li>
          ))}
        </ul>
        <TextField
          label={fill(text.copyUsername, { username: account.username })}
          name="closure_username"
          value={username}
          onChange={setUsername}
          autoComplete="off"
          invalid={code === "confirmation_mismatch"}
          disabled={action.busy}
        />
        {methods.password && (
          <TextField
            label={labels.profile.edit.currentPassword}
            name="closure_password"
            type="password"
            value={password}
            onChange={setPassword}
            autoComplete="current-password"
            invalid={code === "wrong_password"}
            disabled={action.busy}
          />
        )}
        <FormStatus action={action} success={wording.done} />
        <div className="flex flex-wrap justify-end gap-3">
          <button
            type="button"
            autoFocus
            onClick={onClose}
            disabled={action.busy}
            className="border-line-strong font-display text-ink min-h-11 cursor-pointer rounded-xs border px-5 text-[12px] font-bold tracking-[2px] hover:brightness-125 disabled:cursor-wait disabled:opacity-60"
          >
            {labels.profile.edit.cancel}
          </button>
          <button
            type="submit"
            disabled={!ready || action.busy}
            aria-busy={action.busy}
            className="from-blood-from to-blood-to border-blood-line font-display text-ink-bright min-h-11 cursor-pointer rounded-xs border bg-linear-to-b px-5 text-[12px] font-bold tracking-[2px] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {wording.confirm}
          </button>
        </div>
      </form>
    </dialog>
  );
}
