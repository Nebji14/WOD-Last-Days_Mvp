"use client";

/**
 * Ligne de message du chat.
 *
 * - Nom du MJ en cuivre, nom d'un joueur en or ; mention « (modifié) » si besoin.
 * - Un message supprimé sous les yeux du lecteur laisse une trace pendant
 *   {@link DELETED_TRACE_MS} ms, puis disparaît pour ne pas encombrer le chat.
 *   Un message déjà supprimé au chargement n'est pas affiché.
 * - « Modifier » et « Supprimer » apparaissent au survol : sur ses propres
 *   messages pour un joueur, sur tous pour le MJ. Le serveur revérifie ce droit.
 */
import { type FormEvent, useEffect, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorLabel, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

import { type ChatMessage, deleteMessage, editMessage, MESSAGE_MAX_LENGTH } from "../api";
import { useChatStore } from "../store";

interface MessageRowProps {
  readonly message: ChatMessage;
  /** Le lecteur peut modifier et supprimer ce message. */
  readonly canModerate: boolean;
  /** `false` dans l'aperçu du chat replié : aucune action. */
  readonly interactive: boolean;
}

type Mode = "idle" | "editing" | "confirming";

/** Durée d'affichage de la trace d'un message supprimé. */
const DELETED_TRACE_MS = 5000;

const ACTION =
  "font-display cursor-pointer text-[9px] font-bold tracking-[1.5px] hover:brightness-125";

export function AuthorName({ message }: { readonly message: ChatMessage }) {
  return (
    <span className={message.author.role === "gm" ? "text-gm" : "text-gold"}>
      {message.author.displayName} :{" "}
    </span>
  );
}

export function MessageRow({ message, canModerate, interactive }: MessageRowProps) {
  const text = labels.chat;
  const [mode, setMode] = useState<Mode>("idle");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const isDeleted = message.deletedBy !== null;
  const [deletedOnArrival] = useState(isDeleted);
  const [traceExpired, setTraceExpired] = useState(false);

  useEffect(() => {
    if (!isDeleted || deletedOnArrival) {
      return;
    }
    const timer = window.setTimeout(() => setTraceExpired(true), DELETED_TRACE_MS);
    return () => window.clearTimeout(timer);
  }, [isDeleted, deletedOnArrival]);

  if (isDeleted) {
    if (deletedOnArrival || traceExpired) {
      return null;
    }
    return (
      <p className="text-ink-faint text-sm leading-[17px] font-medium italic">
        ⊘ {message.deletedBy === "gm" ? text.deletedByGm : text.deleted}
      </p>
    );
  }

  /** Applique une action, puis range le message renvoyé par le serveur. */
  async function run(action: () => Promise<ChatMessage>): Promise<void> {
    setBusy(true);
    setErrorCode(null);
    try {
      useChatStore.getState().upsert(await action());
      setMode("idle");
    } catch (error) {
      setErrorCode(error instanceof ApiError ? error.code : "internal_error");
    } finally {
      setBusy(false);
    }
  }

  function handleEdit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const body = draft.trim();
    if (body === "" || body === message.body) {
      setMode("idle");
      return;
    }
    void run(() => editMessage(message.id, body));
  }

  function cancel(): void {
    setMode("idle");
    setErrorCode(null);
  }

  if (mode === "editing") {
    return (
      <form
        onSubmit={handleEdit}
        className="border-gold/50 flex flex-col gap-1.5 rounded-sm border bg-[#1e1813] px-2.5 py-2"
      >
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => event.key === "Escape" && cancel()}
          maxLength={MESSAGE_MAX_LENGTH}
          aria-label={text.editLabel}
          disabled={busy}
          autoFocus
          className="border-line bg-panel text-ink focus:border-gold h-7 rounded-xs border px-2 text-[15px] font-medium outline-none"
        />
        {errorCode !== null && <p className="text-danger text-sm">{errorLabel(errorCode)}</p>}
        <div className="flex justify-end gap-[18px]">
          <button type="submit" disabled={busy} className={`${ACTION} text-gold`}>
            {text.save}
          </button>
          <button type="button" onClick={cancel} className={`${ACTION} text-ink-muted`}>
            {text.cancel}
          </button>
        </div>
      </form>
    );
  }

  const showActions = interactive && canModerate;
  return (
    <div
      className={
        showActions
          ? "group hover:border-gold/50 focus-within:border-gold/50 -mx-2.5 rounded-sm border border-transparent px-2.5 hover:bg-[#1e1813] hover:py-2 focus-within:bg-[#1e1813] focus-within:py-2"
          : ""
      }
    >
      <p className="text-ink text-[15px] leading-[19px] font-medium break-words">
        <AuthorName message={message} />
        {message.body}
        {message.edited && <span className="text-ink-muted"> {text.edited}</span>}
      </p>
      {errorCode !== null && <p className="text-danger text-sm">{errorLabel(errorCode)}</p>}
      {showActions && mode === "idle" && (
        <div className="mt-1.5 hidden justify-end gap-[18px] group-focus-within:flex group-hover:flex">
          <button
            type="button"
            onClick={() => {
              setDraft(message.body ?? "");
              setMode("editing");
            }}
            className={`${ACTION} text-gold`}
          >
            ✎ {text.edit}
          </button>
          <button
            type="button"
            onClick={() => setMode("confirming")}
            className={`${ACTION} text-danger`}
          >
            ✕ {text.delete}
          </button>
        </div>
      )}
      {showActions && (
        <ConfirmDialog
          open={mode === "confirming"}
          title={text.confirmDeleteTitle}
          question={text.confirmDelete}
          confirmLabel={text.delete}
          cancelLabel={text.cancel}
          onConfirm={() => {
            if (!busy) void run(() => deleteMessage(message.id));
          }}
          onCancel={cancel}
        />
      )}
    </div>
  );
}
