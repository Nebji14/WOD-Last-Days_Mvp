"use client";

/**
 * Étape 4 de la création : exactement trois spécialités, chacune sur une
 * compétence dotée d'au moins un point (06-É4, RM-004). Seules ces
 * compétences sont proposées.
 */
import type { Dispatch } from "react";

import { CATEGORIES, SKILLS, type SkillName } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

import type { CreationAction, CreationState } from "../useCreationWizard";
import { INPUT, SMALL_LABEL, STEP_HINT, STEP_TITLE } from "./styles";

const LABEL_MAX = 100;

interface SpecialtiesStepProps {
  readonly state: CreationState;
  readonly dispatch: Dispatch<CreationAction>;
}

export function SpecialtiesStep({ state, dispatch }: SpecialtiesStepProps) {
  const text = labels.creation.specialties;
  const available = CATEGORIES.flatMap((category) => SKILLS[category]).filter(
    (skill) => (state.traits.skills[skill] ?? 0) >= 1,
  );

  return (
    <div>
      <h2 className={STEP_TITLE}>{text.title}</h2>
      <p className={STEP_HINT}>{text.hint}</p>
      <ol className="mt-6 flex flex-col gap-5">
        {state.specialties.map((specialty, index) => {
          const number = fill(text.number, { number: index + 1 });
          return (
            <li key={index} className="grid grid-cols-[260px_minmax(0,1fr)] gap-5">
              <label>
                <span className={SMALL_LABEL}>{text.skill}</span>
                <select
                  aria-label={`${number} — ${text.skill}`}
                  value={specialty.skill}
                  onChange={(event) =>
                    dispatch({
                      type: "specialty",
                      index,
                      value: { ...specialty, skill: event.target.value as SkillName | "" },
                    })
                  }
                  className={`${INPUT} mt-1.5 cursor-pointer`}
                >
                  <option value="">{text.choose}</option>
                  {available.map((skill) => (
                    <option key={skill} value={skill}>
                      {labels.skills[skill]} ({state.traits.skills[skill]})
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className={SMALL_LABEL}>{text.label}</span>
                <input
                  aria-label={`${number} — ${text.label}`}
                  value={specialty.label}
                  maxLength={LABEL_MAX}
                  placeholder={text.placeholder}
                  onChange={(event) =>
                    dispatch({
                      type: "specialty",
                      index,
                      value: { ...specialty, label: event.target.value },
                    })
                  }
                  className={`${INPUT} mt-1.5`}
                />
              </label>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
