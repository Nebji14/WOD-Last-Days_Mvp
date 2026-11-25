"use client";

/**
 * Fenêtre de la photo d'une forme : choisir une photo, la repositionner, la
 * retirer. Rien n'est enregistré avant « ENREGISTRER ».
 */
import { type ChangeEvent, useEffect, useId, useRef, useState } from "react";

import { ApiError } from "@/shared/api/client";
import { errorLabel, fill, labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

import {
  cropPortrait,
  openExisting,
  openFile,
  PORTRAIT_ACCEPT,
  type PortraitFiles,
  type PortraitSource,
} from "../portrait";
import { initialCrop, type SquareCrop } from "../portraitCrop";
import { PortraitCropper } from "./PortraitCropper";

const BUTTON =
  "font-display flex min-h-11 cursor-pointer items-center justify-center rounded-xs border px-4 text-[12px] font-bold tracking-[2px] hover:brightness-125 disabled:cursor-wait disabled:opacity-60";
const OUTLINE = `${BUTTON} border-line-strong text-ink`;
const GOLD = `${BUTTON} border-gold text-gold`;
const RED = `${BUTTON} from-blood-from to-blood-to border-blood-line text-ink-bright bg-linear-to-b shadow-[0_0_12px_rgb(216_53_44/0.33)]`;

interface Framing {
  readonly source: PortraitSource;
  readonly crop: SquareCrop;
}

interface PortraitDialogProps {
  /** Nom du fichier de l'image actuelle, `null` sans image. */
  readonly portrait: string | null;
  /** Nom du personnage ou de la forme. */
  readonly name: string;
  readonly onSave: (files: PortraitFiles) => void;
  readonly onRemove: () => void;
  readonly onClose: () => void;
}

function errorCodeOf(error: unknown): string {
  return error instanceof ApiError ? error.code : "internal_error";
}

export function PortraitDialog(props: PortraitDialogProps) {
  const { portrait, name, onSave, onRemove, onClose } = props;
  const text = labels.sheet.portrait;
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const inputId = useId();
  const [framing, setFraming] = useState<Framing | null>(null);
  const [loading, setLoading] = useState(portrait !== null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog !== null && !dialog.open) {
      dialog.showModal();
    }
  }, []);

  useEffect(() => {
    if (portrait === null) {
      return;
    }
    let active = true;
    openExisting(portrait)
      .then((source) => {
        if (active) {
          setFraming({ source, crop: initialCrop(source.bitmap) });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setErrorCode(errorCodeOf(error));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [portrait]);

  async function choose(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0];
    // Vidé pour pouvoir choisir deux fois de suite le même fichier.
    event.target.value = "";
    if (file === undefined) {
      return;
    }
    setLoading(true);
    setErrorCode(null);
    try {
      const source = await openFile(file);
      setFraming({ source, crop: initialCrop(source.bitmap) });
    } catch (error) {
      setErrorCode(errorCodeOf(error));
    } finally {
      setLoading(false);
    }
  }

  async function save(current: Framing): Promise<void> {
    setLoading(true);
    try {
      onSave(await cropPortrait(current.source, current.crop));
    } catch (error) {
      setErrorCode(errorCodeOf(error));
      setLoading(false);
    }
  }

  return (
    <>
      <dialog
        ref={dialogRef}
        aria-labelledby={titleId}
        onCancel={(event) => {
          event.preventDefault();
          onClose();
        }}
        className="bg-panel border-line-strong text-ink m-auto w-[420px] max-w-[calc(100vw-32px)] rounded-xs border p-0 shadow-[0_0_40px_rgb(0_0_0/0.8)] backdrop:bg-black/70"
      >
        <div className="flex flex-col gap-5 px-6 py-6">
          <h2
            id={titleId}
            className="font-display text-copper-light text-[13px] font-bold tracking-[3px]"
          >
            {fill(text.dialogTitle, { name: name.toUpperCase() })}
          </h2>

          {framing === null ? (
            <p className="border-line text-ink-muted flex min-h-40 items-center justify-center rounded-xs border border-dashed px-6 text-center text-lg italic">
              {loading ? text.loading : text.empty}
            </p>
          ) : (
            <PortraitCropper
              bitmap={framing.source.bitmap}
              crop={framing.crop}
              onCrop={(crop) => setFraming({ source: framing.source, crop })}
            />
          )}
          {errorCode !== null && (
            <p role="alert" className="text-danger text-center text-[16px] font-semibold">
              {errorLabel(errorCode)}
            </p>
          )}

          <div className="flex flex-wrap gap-3">
            <input
              id={inputId}
              type="file"
              accept={PORTRAIT_ACCEPT}
              onChange={(event) => void choose(event)}
              disabled={loading}
              className="peer sr-only"
            />
            <label
              htmlFor={inputId}
              className={`${GOLD} peer-focus-visible:outline-gold flex-1 peer-focus-visible:outline-2`}
            >
              {framing === null ? text.choose : text.chooseOther}
            </label>
            {portrait !== null && (
              <button
                type="button"
                onClick={() => setConfirming(true)}
                disabled={loading}
                className={`${BUTTON} border-danger text-danger`}
              >
                {text.removeAction}
              </button>
            )}
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className={`${OUTLINE} flex-1`}>
              {labels.sheet.cancel}
            </button>
            <button
              type="button"
              disabled={loading || framing === null}
              onClick={() => framing !== null && void save(framing)}
              className={`${RED} flex-1`}
            >
              {text.save}
            </button>
          </div>
        </div>
      </dialog>
      <ConfirmDialog
        open={confirming}
        title={labels.sheet.confirmDeleteTitle}
        question={text.confirmRemove}
        confirmLabel={labels.sheet.deleteAction}
        cancelLabel={labels.sheet.cancel}
        onConfirm={() => {
          setConfirming(false);
          onRemove();
        }}
        onCancel={() => setConfirming(false)}
      />
    </>
  );
}
