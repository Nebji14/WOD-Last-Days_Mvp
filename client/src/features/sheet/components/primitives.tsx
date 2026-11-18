"use client";

/**
 * Briques communes des panneaux de la fiche.
 *
 * Deux modes : consultation (lecture seule, sans champ encadré) et
 * modification (champs encadrés, enregistrés dès qu'on les quitte).
 */
import { createContext, type ReactNode, useContext, useState } from "react";

import type { Character, Sheet } from "@/features/characters/model";
import type { NpcCategory } from "@/features/npcs/api";
import { labels } from "@/shared/i18n";
import { ConfirmDialog } from "@/shared/ui/ConfirmDialog";

import type { RunAction } from "../useSheetController";

interface SheetContextValue {
  readonly character: Character;
  /** Forme affichée (onglet actif). */
  readonly sheet: Sheet;
  /** M2 : la fiche est en cours de modification. */
  readonly editing: boolean;
  readonly run: RunAction;
  /** Catégories de PNJ, pour la fiche d'un PNJ ; vide pour un personnage joueur. */
  readonly npcCategories: readonly NpcCategory[];
}

const SheetContext = createContext<SheetContextValue | null>(null);
export const SheetProvider = SheetContext.Provider;

export function useSheet(): SheetContextValue {
  const value = useContext(SheetContext);
  if (value === null) {
    throw new Error("useSheet doit être appelé dans une fiche");
  }
  return value;
}

export const PANEL = "bg-seat border-line relative rounded-md border";
export const PANEL_TITLE = "font-display text-copper text-[11px] font-bold tracking-[3px]";
export const SMALL_LABEL = "font-display text-gold text-[9px] font-bold tracking-[2px]";
export const COLUMN_LABEL = "font-display text-ink-muted text-[8px] font-bold tracking-[1.2px]";
export const LINK_ACTION =
  "font-display text-gold cursor-pointer text-[9px] font-bold tracking-[2px] hover:brightness-125";
const FIELD_FRAME =
  "border-line-strong bg-panel text-ink focus:border-gold rounded-xs border px-1.5 outline-none";

interface PanelProps {
  readonly title: string;
  readonly children: ReactNode;
  /** Élément placé à droite du titre : lien d'ajout, rappel de capacité… */
  readonly aside?: ReactNode;
  readonly className?: string;
}

export function Panel({ title, children, aside, className = "" }: PanelProps) {
  return (
    <section className={`${PANEL} px-5 pt-4 pb-4 ${className}`}>
      <header className="mb-3 flex items-center justify-between gap-3">
        <h2 className={PANEL_TITLE}>{title}</h2>
        {aside}
      </header>
      {children}
    </section>
  );
}

interface DotsProps {
  readonly label: string;
  readonly value: number;
  readonly max: number;
  /** Valeur plancher : 1 pour un attribut, 0 pour une compétence. */
  readonly min: number;
  /** Absent en consultation : les points ne sont pas cliquables. */
  readonly onChange?: (value: number) => void;
}

/**
 * Points ●○ d'un attribut ou d'une compétence.
 *
 * En modification, cliquer le n-ième point donne la valeur n ; cliquer
 * le point de la valeur actuelle donne n − 1.
 */
export function Dots({ label, value, max, min, onChange }: DotsProps) {
  const dots = Array.from({ length: max }, (_, index) => index + 1);
  const dotClass = (rank: number): string =>
    `size-2.5 rounded-full ${rank <= value ? "bg-gold" : "border-gold/70 border"}`;

  if (onChange === undefined) {
    return (
      <span role="img" aria-label={`${label} : ${value}`} className="flex gap-[3px]">
        {dots.map((rank) => (
          <span key={rank} aria-hidden="true" className={dotClass(rank)} />
        ))}
      </span>
    );
  }
  return (
    <span role="group" aria-label={`${label} : ${value}`} className="flex gap-[3px]">
      {dots.map((rank) => (
        <button
          key={rank}
          type="button"
          aria-label={`${label} ${rank}`}
          onClick={() => onChange(Math.max(min, rank === value ? rank - 1 : rank))}
          className={`${dotClass(rank)} cursor-pointer hover:brightness-150`}
        />
      ))}
    </span>
  );
}

interface TextValueProps {
  readonly label: string;
  readonly value: string;
  readonly editing: boolean;
  readonly onCommit: (value: string) => void;
  readonly maxLength: number;
  readonly placeholder?: string;
  /** Classes de taille et de style du texte, communes aux deux modes. */
  readonly className?: string;
  readonly multiline?: boolean;
}

/**
 * Texte d'un champ : affiché tel quel en consultation, saisi dans un champ
 * encadré en modification. La saisie est enregistrée en quittant le champ ou
 * avec Entrée (champ d'une ligne).
 *
 * Le champ est recréé quand la valeur du serveur change, pour afficher une
 * modification venue d'ailleurs.
 */
export function TextValue(props: TextValueProps) {
  const { label, value, editing, onCommit, maxLength, placeholder, multiline } = props;
  const className = props.className ?? "";

  if (!editing) {
    return (
      <span className={`${className} ${multiline ? "whitespace-pre-wrap" : ""}`}>
        {value || "—"}
      </span>
    );
  }
  const commit = (next: string): void => {
    if (next.trim() !== value) {
      onCommit(next.trim());
    }
  };
  if (multiline) {
    return (
      <textarea
        key={value}
        defaultValue={value}
        aria-label={label}
        maxLength={maxLength}
        placeholder={placeholder}
        onBlur={(event) => commit(event.target.value)}
        className={`${FIELD_FRAME} ${className} w-full resize-y py-1`}
      />
    );
  }
  return (
    <input
      key={value}
      type="text"
      defaultValue={value}
      aria-label={label}
      maxLength={maxLength}
      placeholder={placeholder}
      onBlur={(event) => commit(event.target.value)}
      onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
      className={`${FIELD_FRAME} ${className} w-full min-w-0`}
    />
  );
}

interface NumberValueProps {
  readonly label: string;
  readonly value: number;
  readonly editing: boolean;
  readonly onCommit: (value: number) => void;
  readonly min: number;
  readonly max: number;
  readonly className?: string;
}

const STEP_BUTTON =
  "border-line-strong text-gold hover:border-gold flex size-7 cursor-pointer items-center justify-center rounded-xs border text-base leading-none font-bold disabled:cursor-not-allowed disabled:opacity-35";
/** Délai après lequel un clic sans réponse du serveur libère les boutons. */
const STEP_RELEASE_MS = 3000;

/**
 * Nombre d'un champ : affiché en consultation ; en modification, boutons − et +
 * enregistrés à chaque clic, et saisie directe enregistrée dès qu'on quitte le
 * champ ou qu'on appuie sur Entrée.
 */
export function NumberValue(props: NumberValueProps) {
  const { label, value, editing, onCommit, min, max, className = "" } = props;
  // Valeur demandée au serveur : les boutons attendent qu'elle revienne.
  const [requested, setRequested] = useState<number | null>(null);
  const waiting = requested !== null && requested !== value;

  if (!editing) {
    return <span className={className}>{value}</span>;
  }

  function step(next: number): void {
    setRequested(next);
    window.setTimeout(() => setRequested(null), STEP_RELEASE_MS);
    onCommit(next);
  }

  return (
    <span className="inline-flex items-center gap-1">
      <button
        type="button"
        aria-label={`${label} −1`}
        disabled={waiting || value <= min}
        onClick={() => step(value - 1)}
        className={STEP_BUTTON}
      >
        −
      </button>
      <input
        key={value}
        type="text"
        inputMode="numeric"
        defaultValue={value}
        aria-label={label}
        onBlur={(event) => {
          const next = Number.parseInt(event.target.value, 10);
          if (Number.isNaN(next) || next < min || next > max) {
            event.target.value = String(value);
          } else if (next !== value) {
            onCommit(next);
          }
        }}
        onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
        className={`${FIELD_FRAME} ${className} h-7 w-11 text-center`}
      />
      <button
        type="button"
        aria-label={`${label} +1`}
        disabled={waiting || value >= max}
        onClick={() => step(value + 1)}
        className={STEP_BUTTON}
      >
        +
      </button>
    </span>
  );
}

interface ConfirmDeleteProps {
  /** Nom accessible du bouton : ce qui va être supprimé. */
  readonly label: string;
  readonly onConfirm: () => void;
  /** Question posée avant la suppression. */
  readonly question?: string;
  /** Texte du déclencheur à la place de l'icône ✕ (lien « Supprimer la note »). */
  readonly trigger?: string;
}

/**
 * Suppression en deux temps : le déclencheur ouvre une fenêtre de
 * confirmation modale ; rien n'est supprimé avant « SUPPRIMER ».
 */
export function ConfirmDelete({ label, onConfirm, question, trigger }: ConfirmDeleteProps) {
  const [asking, setAsking] = useState(false);
  const text = labels.sheet;

  return (
    <>
      <button
        type="button"
        aria-label={label}
        title={label}
        onClick={() => setAsking(true)}
        className={`text-danger cursor-pointer px-1 hover:brightness-125 ${
          trigger === undefined ? "text-sm" : "font-display text-[9px] font-bold tracking-[2px]"
        }`}
      >
        {trigger ?? "✕"}
      </button>
      <ConfirmDialog
        open={asking}
        title={text.confirmDeleteTitle}
        question={question ?? text.confirmDelete}
        confirmLabel={text.deleteAction}
        cancelLabel={text.cancel}
        onConfirm={() => {
          setAsking(false);
          onConfirm();
        }}
        onCancel={() => setAsking(false)}
      />
    </>
  );
}
