"use client";

/**
 * Saisie de la recette de jet d'un pouvoir, d'une arme ou d'un atout.
 *
 * Deux traits au minimum à l'écran, d'autres s'ajoutent à la demande, puis
 * le coût en Volonté. Chaque trait montre sa valeur actuelle sur la fiche ;
 * l'Avantage surnaturel vaut le niveau inscrit au recto. Un nouveau pouvoir
 * le propose d'office. Une recette sans aucun trait choisi n'est pas
 * enregistrée : l'élément n'a alors pas de jet. Le malus et le bonus du MJ
 * se saisissent au moment du jet, pas ici.
 */
import type { EntryKind, RollRecipe } from "@/features/characters/model";
import { ATTRIBUTES, CATEGORIES, SKILLS } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { SPECIAL_PARTS } from "../pool";

const MIN_SLOTS = 2;
const MAX_SLOTS = 8;
const COST_MAX = 5;

/** Recette en cours de saisie : des emplacements vides sont permis. */
export interface RecipeDraft {
  readonly parts: readonly string[];
  readonly willpower_cost: number;
  readonly bonus: number;
}

export function draftOf(recipe: RollRecipe | null | undefined, kind: EntryKind): RecipeDraft {
  const parts =
    recipe == null && kind === "power" ? ["", "", "supernatural"] : [...(recipe?.parts ?? [])];
  while (parts.length < MIN_SLOTS) {
    parts.push("");
  }
  return { parts, willpower_cost: recipe?.willpower_cost ?? 0, bonus: recipe?.bonus ?? 0 };
}

/** Recette à enregistrer, ou `null` si aucun trait n'est choisi. */
export function recipeOf(draft: RecipeDraft): RollRecipe | null {
  const parts = draft.parts.filter((part) => part !== "");
  return parts.length === 0 ? null : { ...draft, parts };
}

const SELECT =
  "border-line-strong bg-panel text-ink focus:border-gold h-7 min-w-0 rounded-xs border px-1 text-[14px] outline-none";
const STEP =
  "border-line-strong text-gold hover:border-gold size-6 cursor-pointer rounded-xs border text-sm leading-none font-bold disabled:cursor-not-allowed disabled:opacity-35";

function Stepper(props: {
  readonly label: string;
  readonly value: number;
  readonly min: number;
  readonly max: number;
  readonly onChange: (value: number) => void;
}) {
  const { label, value, min, max, onChange } = props;
  return (
    <span className="text-ink flex items-center gap-1.5 text-[14px]">
      {label}
      <button
        type="button"
        aria-label={`${label} −1`}
        disabled={value <= min}
        onClick={() => onChange(value - 1)}
        className={STEP}
      >
        −
      </button>
      <strong className="text-gold w-6 text-center">{value}</strong>
      <button
        type="button"
        aria-label={`${label} +1`}
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
        className={STEP}
      >
        +
      </button>
    </span>
  );
}

interface RecipeEditorProps {
  readonly kind: EntryKind;
  readonly draft: RecipeDraft;
  readonly onChange: (draft: RecipeDraft) => void;
  /** Valeur actuelle d'un trait sur la fiche, affichée dans la liste. */
  readonly valueOf: (part: string) => number;
}

export function RecipeEditor({ kind, draft, onChange, valueOf }: RecipeEditorProps) {
  const text = labels.dice.recipe;
  const special = SPECIAL_PARTS.filter((part) => part !== "weapon_bonus" || kind === "weapon");
  const setPart = (index: number, value: string) =>
    onChange({ ...draft, parts: draft.parts.map((part, at) => (at === index ? value : part)) });

  return (
    <fieldset className="border-line-soft mt-2 flex flex-col gap-2 border-t pt-2">
      <legend className="font-display text-gold pr-2 text-[9px] font-bold tracking-[2px]">
        {text.title}
      </legend>
      <p className="text-ink-muted text-[13px] italic">{text.hint}</p>
      <div className="flex flex-wrap items-center gap-1.5">
        {draft.parts.map((part, index) => (
          <span key={index} className="flex items-center gap-1">
            {index > 0 && <span className="text-ink-muted">+</span>}
            <select
              value={part}
              aria-label={`${text.title} ${index + 1}`}
              onChange={(event) => setPart(index, event.target.value)}
              className={SELECT}
            >
              <option value="">{text.none}</option>
              <optgroup label={text.groups.special}>
                {special.map((name) => (
                  <option key={name} value={name}>
                    {labels.dice.parts[name]} · {valueOf(name)}
                  </option>
                ))}
              </optgroup>
              <optgroup label={text.groups.attributes}>
                {CATEGORIES.flatMap((category) => ATTRIBUTES[category]).map((name) => (
                  <option key={name} value={name}>
                    {labels.attributes[name]} · {valueOf(name)}
                  </option>
                ))}
              </optgroup>
              <optgroup label={text.groups.skills}>
                {CATEGORIES.flatMap((category) => SKILLS[category]).map((name) => (
                  <option key={name} value={name}>
                    {labels.skills[name]} · {valueOf(name)}
                  </option>
                ))}
              </optgroup>
            </select>
            {index >= MIN_SLOTS && (
              <button
                type="button"
                aria-label={text.removePart}
                onClick={() =>
                  onChange({ ...draft, parts: draft.parts.filter((_, at) => at !== index) })
                }
                className="text-danger cursor-pointer px-0.5 text-sm"
              >
                ✕
              </button>
            )}
          </span>
        ))}
        {draft.parts.length < MAX_SLOTS && (
          <button
            type="button"
            onClick={() => onChange({ ...draft, parts: [...draft.parts, ""] })}
            className="font-display text-gold cursor-pointer px-1 text-[9px] font-bold tracking-[2px] hover:brightness-125"
          >
            {text.addPart}
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-5">
        <Stepper
          label={text.cost}
          value={draft.willpower_cost}
          min={0}
          max={COST_MAX}
          onChange={(value) => onChange({ ...draft, willpower_cost: value })}
        />
      </div>
    </fieldset>
  );
}
