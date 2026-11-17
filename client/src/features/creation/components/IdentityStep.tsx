"use client";

/** Étape 1 de la création : identité, seul le nom est obligatoire (06-É1). */
import type { Dispatch } from "react";

import { labels } from "@/shared/i18n";

import { type CreationAction, type CreationState, IDENTITY_FIELDS } from "../useCreationWizard";
import { INPUT, SMALL_LABEL, STEP_HINT, STEP_TITLE } from "./styles";

const MAX_LENGTH = { name: 80, other: 120 } as const;

interface IdentityStepProps {
  readonly state: CreationState;
  readonly dispatch: Dispatch<CreationAction>;
}

export function IdentityStep({ state, dispatch }: IdentityStepProps) {
  const text = labels.creation.identity;
  const fieldLabels = labels.sheet.identity;

  return (
    <div>
      <h2 className={STEP_TITLE}>{text.title}</h2>
      <p className={STEP_HINT}>{text.hint}</p>
      <div className="mt-6 grid grid-cols-2 gap-x-6 gap-y-5">
        {IDENTITY_FIELDS.map((field) => (
          <label key={field} className={field === "name" ? "col-span-2" : ""}>
            <span className={SMALL_LABEL}>{fieldLabels[field].toUpperCase()}</span>
            <input
              value={state.identity[field]}
              required={field === "name"}
              autoFocus={field === "name"}
              maxLength={field === "name" ? MAX_LENGTH.name : MAX_LENGTH.other}
              onChange={(event) => dispatch({ type: "identity", field, value: event.target.value })}
              className={`${INPUT} mt-1.5 ${field === "name" ? "h-11 text-xl" : ""}`}
            />
          </label>
        ))}
      </div>
    </div>
  );
}
