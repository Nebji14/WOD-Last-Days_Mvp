"use client";

/**
 * [Panneau — Caractéristiques] du recto (05a).
 *
 * Deux colonnes (RM-005) : BASE, calculée par le serveur et jamais stockée, et
 * EFFECTIVE, saisie librement et seule conservée. Modifier un attribut recalcule
 * la base sans toucher à l'effective. La protection globale se saisit à la
 * main, sans aucun calcul (RM-024). PNJ simplifié : aucune base calculée,
 * colonne BASE à « — » (RM-022).
 */
import { setSheetField } from "@/features/characters/api";
import { isSimplifiedNpc } from "@/features/characters/model";
import { labels } from "@/shared/i18n";

import { COLUMN_LABEL, NumberValue, Panel, TextValue, useSheet } from "./primitives";

const STATS = ["size", "speed", "defense", "initiative"] as const;
const ROW = "grid h-7 grid-cols-[minmax(0,1fr)_56px_70px] items-center gap-x-2";

export function StatsPanel() {
  const { character, sheet, editing, run } = useSheet();
  const text = labels.sheet.stats;
  const noBase = isSimplifiedNpc(character);

  return (
    <Panel title={text.title}>
      <div className={`${ROW} -mt-6 mb-1 h-4`}>
        <span />
        <span className={`${COLUMN_LABEL} text-center`}>{text.base}</span>
        <span className={`${COLUMN_LABEL} text-gold text-center`}>{text.effective}</span>
      </div>
      {STATS.map((stat) => (
        <div key={stat} className={ROW}>
          <span className="text-ink text-base font-semibold">{text[stat]}</span>
          <span className="text-ink-muted text-center text-base font-medium">
            {noBase ? "—" : sheet.base[stat]}
          </span>
          <span className="flex justify-center">
            <NumberValue
              label={`${text[stat]} — ${text.effective}`}
              value={sheet.effective[stat]}
              editing={editing}
              min={0}
              max={99}
              onCommit={(value) =>
                void run(() => setSheetField(sheet.id, stat, value, sheet.effective[stat]))
              }
              className="text-ink-bright text-base font-bold"
            />
          </span>
        </div>
      ))}
      <div className={ROW}>
        <span className="text-ink text-base font-semibold">{text.globalProtection}</span>
        <span className="text-ink-muted text-center text-base font-medium">—</span>
        <span className="flex justify-center">
          <TextValue
            label={text.globalProtection}
            value={sheet.texts.global_protection ?? ""}
            editing={editing}
            maxLength={60}
            onCommit={(value) =>
              void run(() =>
                setSheetField(
                  sheet.id,
                  "global_protection",
                  value,
                  sheet.texts.global_protection ?? "",
                ),
              )
            }
            className="text-ink-bright block text-center text-base font-bold"
          />
        </span>
      </div>
      <p className="text-ink-faint mt-2 text-[13px] font-medium italic">
        {noBase ? labels.npcSheet.noBase : text.reminder}
      </p>
    </Panel>
  );
}
