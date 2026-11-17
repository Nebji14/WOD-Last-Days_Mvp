"use client";

/**
 * Disposition des faces RECTO et VERSO de la fiche.
 *
 * Recto : identité, attributs, moralité, avantage surnaturel, santé, volonté,
 * caractéristiques, puis compétences. Verso : listes, tactiques et expérience à
 * gauche ; équipement et description à droite.
 *
 * Pour un PNJ simplifié, Puissance / Finesse / Résilience et les notes du PNJ
 * remplacent attributs et compétences ; un PNJ complet garde le recto normal
 * avec ses notes en dessous. Le verso d'un PNJ n'a ni tactiques ni expérience.
 */
import { isSimplifiedNpc } from "@/features/characters/model";

import { DescriptionPanel } from "./DescriptionPanel";
import { EntryPanel } from "./EntryPanel";
import { ExperiencePanel } from "./ExperiencePanel";
import { HealthPanel, WillpowerPanel } from "./GaugePanels";
import { IdentityPanel } from "./IdentityPanel";
import { NpcDeleteLink, NpcNotesPanel, SimplifiedTraitsPanel } from "./NpcPanels";
import { useSheet } from "./primitives";
import { MoralityPanel, SupernaturalPanel } from "./ScalePanels";
import { StatsPanel } from "./StatsPanel";
import { TacticsPanel } from "./TacticsPanel";
import { AttributesPanel, SkillsPanel } from "./TraitPanels";

export function RectoFace() {
  const { character } = useSheet();
  const isNpc = character.npc != null;

  if (isSimplifiedNpc(character)) {
    return (
      <div className="flex flex-col gap-4">
        <IdentityPanel />
        <div className="grid grid-cols-[minmax(0,1fr)_364px] gap-4">
          <div className="flex flex-col gap-4">
            <SimplifiedTraitsPanel />
            <NpcNotesPanel />
          </div>
          <div className="flex flex-col gap-4">
            <HealthPanel />
            <WillpowerPanel />
            <MoralityPanel />
            <StatsPanel />
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <IdentityPanel />
      <div className="grid grid-cols-[minmax(0,1fr)_364px] gap-4">
        <div className="flex flex-col gap-4">
          <AttributesPanel />
          <MoralityPanel />
          <SupernaturalPanel />
        </div>
        <div className="flex flex-col gap-4">
          <HealthPanel />
          <WillpowerPanel />
          <StatsPanel />
        </div>
      </div>
      <SkillsPanel />
      {isNpc && <NpcNotesPanel />}
    </div>
  );
}

export function VersoFace() {
  const { character } = useSheet();
  const isNpc = character.npc != null;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 items-start gap-4">
        <div className="flex flex-col gap-4">
          <EntryPanel kind="merit" />
          <EntryPanel kind="flaw" />
          <EntryPanel kind="power" />
          {!isNpc && <TacticsPanel />}
          {!isNpc && <ExperiencePanel />}
        </div>
        <div className="flex flex-col gap-4">
          <EntryPanel kind="weapon" />
          <EntryPanel kind="armor" />
          <EntryPanel kind="item" />
          <DescriptionPanel />
        </div>
      </div>
      <NpcDeleteLink />
    </div>
  );
}
