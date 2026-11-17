"use client";

/**
 * [Panneau — Attributs] et [Panneau — Compétences] du recto (05a).
 *
 * Attributs : 5 points affichés, 10 pour un personnage éveillé. Avant l'éveil,
 * rien ne laisse deviner les points 6 à 10 (05, ÉVEIL V1 à V4).
 * Compétences : nom, champ de spécialités, points (05-I9).
 */
import { setSheetField, setSpecialties } from "@/features/characters/api";
import {
  ATTRIBUTES,
  attributeMax,
  CATEGORIES,
  SKILL_MAX,
  SKILLS,
} from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { Dots, Panel, TextValue, useSheet } from "./primitives";

const GROUP_LABEL = "text-ink-muted mb-1 text-[15px] font-medium italic";

export function AttributesPanel() {
  const { character, sheet, editing, run } = useSheet();
  const max = attributeMax(character);

  return (
    <Panel title={labels.sheet.attributes}>
      <div className="grid grid-cols-3 gap-x-6">
        {CATEGORIES.map((category) => (
          <div key={category}>
            <p className={GROUP_LABEL}>{labels.categories[category]}</p>
            {ATTRIBUTES[category].map((name) => (
              <div key={name} className="flex h-[26px] items-center justify-between gap-2">
                <span className="text-ink text-[17px] font-semibold">
                  {labels.attributes[name]}
                </span>
                <Dots
                  label={labels.attributes[name]}
                  value={sheet.attributes[name]}
                  max={max}
                  min={1}
                  onChange={
                    editing
                      ? (value) =>
                          void run(() =>
                            setSheetField(sheet.id, name, value, sheet.attributes[name]),
                          )
                      : undefined
                  }
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    </Panel>
  );
}

export function SkillsPanel() {
  const { sheet, editing, run } = useSheet();
  const text = labels.sheet;

  return (
    <Panel title={text.skills}>
      <div className="grid grid-cols-3 gap-x-7">
        {CATEGORIES.map((category) => (
          <div key={category}>
            <div className="mb-2 grid grid-cols-[minmax(0,1fr)_112px_62px] items-end gap-x-2.5">
              <p className={`${GROUP_LABEL} mb-0`}>{labels.skillCategories[category]}</p>
              <p className="font-display text-[9px] font-bold tracking-[2px] text-[#7a6f5e]">
                {text.specialty}
              </p>
            </div>
            {SKILLS[category].map((name) => (
              <div
                key={name}
                className="grid h-10 grid-cols-[minmax(0,1fr)_112px_62px] items-center gap-x-2.5"
              >
                <span className="text-ink truncate text-base font-semibold">
                  {labels.skills[name]}
                </span>
                <TextValue
                  label={`${text.specialty} — ${labels.skills[name]}`}
                  value={(sheet.specialties[name] ?? []).join(", ")}
                  editing={editing}
                  onCommit={(value) => void run(() => setSpecialties(sheet.id, name, value))}
                  maxLength={400}
                  placeholder={text.specialtyHint}
                  className="text-copper-light block truncate text-sm font-medium italic"
                />
                <Dots
                  label={labels.skills[name]}
                  value={sheet.skills[name]}
                  max={SKILL_MAX}
                  min={0}
                  onChange={
                    editing
                      ? (value) =>
                          void run(() => setSheetField(sheet.id, name, value, sheet.skills[name]))
                      : undefined
                  }
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    </Panel>
  );
}
