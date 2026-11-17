"use client";

/** Contenu de l'étape en cours de l'assistant de création (06-É1 à É5). */
import type { Dispatch } from "react";

import { type CreationAction, type CreationState, STEPS } from "../useCreationWizard";
import { AllocationStep } from "./AllocationStep";
import { IdentityStep } from "./IdentityStep";
import { SpecialtiesStep } from "./SpecialtiesStep";
import { SummaryStep } from "./SummaryStep";

interface CreationStepBodyProps {
  readonly state: CreationState;
  readonly dispatch: Dispatch<CreationAction>;
}

export function CreationStepBody({ state, dispatch }: CreationStepBodyProps) {
  switch (STEPS[state.step]) {
    case "attributes":
      return <AllocationStep kind="attributes" state={state} dispatch={dispatch} />;
    case "skills":
      return <AllocationStep kind="skills" state={state} dispatch={dispatch} />;
    case "specialties":
      return <SpecialtiesStep state={state} dispatch={dispatch} />;
    case "summary":
      return <SummaryStep state={state} dispatch={dispatch} />;
    default:
      return <IdentityStep state={state} dispatch={dispatch} />;
  }
}
