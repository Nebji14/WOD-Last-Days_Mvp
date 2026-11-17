"use client";

/**
 * Fenêtre de création de personnage.
 *
 * Cinq étapes guidées : identité, attributs, compétences, spécialités,
 * récapitulatif. « Suivant » reste désactivé tant que l'étape n'est pas valide,
 * avec la raison affichée. Une fois le personnage créé, la fenêtre affiche sa
 * fiche. Fermer en cours de route demande confirmation et abandonne la
 * création : aucun brouillon n'est gardé.
 */
import { useEffect, useState } from "react";

import { fetchCurrentAccount } from "@/features/auth/api";
import { createCharacter } from "@/features/characters/api";
import { ApiError } from "@/shared/api/client";
import { errorLabel, fill, labels } from "@/shared/i18n";
import { sheetPath, sheetWindowName } from "@/shared/windows/detached";

import { stepBlocker } from "../blockers";
import { STEPS, toPayload, useCreationWizard } from "../useCreationWizard";
import { CreationFooter } from "./CreationFooter";
import { CreationHeader } from "./CreationHeader";
import { CreationStepBody } from "./CreationStepBody";
import { RulesPanel } from "./RulesPanel";
import { StepTrail } from "./StepTrail";
import { CARD } from "./styles";

export function CreationScreen() {
  const [state, dispatch] = useCreationWizard();
  const [player, setPlayer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const blocker = stepBlocker(state);
  const last = state.step === STEPS.length - 1;

  useEffect(() => {
    document.title = labels.creation.windowTitle;
    fetchCurrentAccount()
      .then((account) => (account === null ? window.close() : setPlayer(account.displayName)))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!state.dirty || busy) {
      return;
    }
    const guard = (event: BeforeUnloadEvent): void => event.preventDefault();
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [state.dirty, busy]);

  const create = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      const character = await createCharacter(toPayload(state));
      window.name = sheetWindowName(character.id);
      window.location.replace(sheetPath(character.id));
    } catch (failure) {
      setBusy(false);
      setError(errorLabel(failure instanceof ApiError ? failure.code : "internal_error"));
    }
  };

  return (
    <div className="bg-night text-ink flex h-screen flex-col">
      <CreationHeader
        subtitle={fill(labels.creation.subtitle, { player, step: state.step + 1 })}
        dirty={state.dirty}
      />
      <StepTrail
        step={state.step}
        reached={state.reached}
        onGoto={(step) => dispatch({ type: "goto", step })}
      />
      <main className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_330px] gap-4 px-8 pt-6">
        <section className={`${CARD} min-h-0 overflow-y-auto px-6 pt-5 pb-5`}>
          <CreationStepBody state={state} dispatch={dispatch} />
        </section>
        <RulesPanel state={state} />
      </main>
      <CreationFooter
        message={error ?? blocker}
        canGoBack={state.step > 0}
        canGoOn={blocker === null && !busy}
        last={last}
        busy={busy}
        onBack={() => dispatch({ type: "goto", step: state.step - 1 })}
        onNext={() => (last ? void create() : dispatch({ type: "goto", step: state.step + 1 }))}
      />
    </div>
  );
}
