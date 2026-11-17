"use client";

/**
 * Étapes « Attributs » et « Compétences » de la création.
 *
 * Une carte par catégorie : choix de la priorité, compteur de points (✓ si
 * complet, « reste n » sinon), puis les traits et leurs points. Pour les
 * attributs, le point gratuit est grisé et une valeur de 4 ou 5 affiche une
 * alerte non bloquante.
 */
import { type Dispatch } from "react";

import { CATEGORIES, type Category } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

import {
  ATTRIBUTE_BUDGETS,
  attributesToDiscuss,
  budget,
  type Rank,
  remaining,
  SKILL_BUDGETS,
  spent,
  TRAIT_BOUNDS,
  type TraitKind,
  traitNames,
} from "../rules";
import type { CreationAction, CreationState } from "../useCreationWizard";
import { CARD, STEP_HINT, STEP_TITLE } from "./styles";

const RANKS: readonly Rank[] = [1, 2, 3];

interface AllocationStepProps {
  readonly kind: TraitKind;
  readonly state: CreationState;
  readonly dispatch: Dispatch<CreationAction>;
}

export function AllocationStep({ kind, state, dispatch }: AllocationStepProps) {
  const text = labels.creation;
  const stepText = kind === "attributes" ? text.attributes : text.skills;
  const trimmed = state.trimmed.map((category) => labels.categories[category]).join(", ");

  return (
    <div className="flex h-full flex-col">
      <h2 className={STEP_TITLE}>{stepText.title}</h2>
      <p className={STEP_HINT}>{stepText.hint}</p>
      {trimmed !== "" && (
        <p role="status" className="text-danger mt-2 text-[15px]">
          {fill(text.trimmed, { categories: trimmed })}
        </p>
      )}
      <div className="mt-5 grid flex-1 grid-cols-3 gap-5">
        {CATEGORIES.map((category) => (
          <CategoryCard
            key={category}
            kind={kind}
            category={category}
            state={state}
            dispatch={dispatch}
          />
        ))}
      </div>
      <p className="text-ink-faint mt-4 text-sm italic">{stepText.footer}</p>
    </div>
  );
}

interface CategoryCardProps extends AllocationStepProps {
  readonly category: Category;
}

function CategoryCard({ kind, category, state, dispatch }: CategoryCardProps) {
  const text = labels.creation;
  const priorities = state.priorities[kind];
  const values = state.traits[kind];
  const total = budget(kind, priorities, category);
  const used = spent(kind, values, category);
  const left = remaining(kind, priorities, values, category);
  const complete = left === 0;
  const names = traitNames(kind, category);
  const title = kind === "attributes" ? labels.categories : labels.skillCategories;
  const alerts =
    kind === "attributes" ? attributesToDiscuss(values).filter((name) => names.includes(name)) : [];

  return (
    <section
      aria-label={title[category]}
      className={`${CARD} flex flex-col px-4 pt-4 pb-4 ${complete ? "" : "border-blood-line/70"}`}
    >
      <h3 className="font-display text-copper-light text-[13px] font-bold tracking-[3px]">
        {title[category].toUpperCase()}
      </h3>
      <div
        role="radiogroup"
        aria-label={fill(text.priorityLabel, { category: title[category] })}
        className="mt-3 flex gap-1.5"
      >
        {RANKS.map((rank) => (
          <button
            key={rank}
            type="button"
            role="radio"
            aria-checked={priorities[category] === rank}
            onClick={() => dispatch({ type: "priority", kind, category, rank })}
            className={`font-display h-7 flex-1 cursor-pointer rounded-xs border text-[9px] font-bold tracking-[1px] ${
              priorities[category] === rank
                ? "border-gold bg-gold text-abyss"
                : "border-line-strong text-ink-muted hover:text-ink"
            }`}
          >
            {priorityLabel(kind, rank)}
          </button>
        ))}
      </div>
      <p className={`mt-3 text-[15px] ${complete ? "text-valid" : "text-danger"}`}>
        {complete
          ? `${fill(text.count, { spent: used, budget: total })} ✓`
          : fill(text.countMissing, { spent: used, budget: total, left })}
      </p>
      <ul className={`mt-3 flex flex-col ${kind === "attributes" ? "gap-3" : "gap-1"}`}>
        {names.map((name) => (
          <li key={name} className="flex items-center justify-between gap-2">
            <span className={`text-ink ${kind === "attributes" ? "text-lg" : "text-base"}`}>
              {traitLabel(kind, name)}
            </span>
            <TraitDots
              kind={kind}
              label={traitLabel(kind, name)}
              value={values[name] ?? 0}
              onPick={(rank) => dispatch({ type: "trait", kind, category, name, rank })}
            />
          </li>
        ))}
      </ul>
      {alerts.map((name) => (
        <p
          key={name}
          role="note"
          className="border-gold bg-gold/10 text-ink mt-4 rounded-xs border px-3 py-2 text-sm"
        >
          ⚠{" "}
          {fill(text.attributes.alert, { trait: traitLabel(kind, name), value: values[name] ?? 0 })}
        </p>
      ))}
    </section>
  );
}

function priorityLabel(kind: TraitKind, rank: Rank): string {
  const points = (kind === "attributes" ? ATTRIBUTE_BUDGETS : SKILL_BUDGETS)[rank];
  const text = labels.creation;
  return rank === 1 ? fill(text.firstPriority, { points }) : fill(text.priority, { rank, points });
}

function traitLabel(kind: TraitKind, name: string): string {
  const source: Readonly<Record<string, string>> =
    kind === "attributes" ? labels.attributes : labels.skills;
  return source[name] ?? name;
}

interface TraitDotsProps {
  readonly kind: TraitKind;
  readonly label: string;
  readonly value: number;
  readonly onPick: (rank: number) => void;
}

/** Points d'un trait ; le point gratuit d'un attribut est grisé et non cliquable. */
function TraitDots({ kind, label, value, onPick }: TraitDotsProps) {
  const { min, max } = TRAIT_BOUNDS[kind];
  const ranks = Array.from({ length: max }, (_, index) => index + 1);

  return (
    <span role="group" aria-label={`${label} : ${value}`} className="flex gap-[3px]">
      {ranks.map((rank) =>
        rank <= min ? (
          <span key={rank} aria-hidden="true" className="bg-copper-deep size-2.5 rounded-full" />
        ) : (
          <button
            key={rank}
            type="button"
            aria-label={`${label} ${rank}`}
            onClick={() => onPick(rank)}
            className={`size-2.5 cursor-pointer rounded-full hover:brightness-150 ${
              rank <= value ? "bg-gold" : "border-gold/70 border"
            }`}
          />
        ),
      )}
    </span>
  );
}
