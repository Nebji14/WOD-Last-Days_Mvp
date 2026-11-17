"use client";

/**
 * Disposition des deux faces de jeu de la fiche.
 *
 * RECTO (05a) : identité, attributs, moralité, avantage surnaturel, santé,
 * volonté, caractéristiques, puis compétences en pleine largeur.
 * VERSO (05b) : listes, tactiques et expérience à gauche ; armes, armures,
 * objets, description et récit à droite.
 */
import { DescriptionPanel } from "./DescriptionPanel";
import { EntryPanel } from "./EntryPanel";
import { ExperiencePanel } from "./ExperiencePanel";
import { HealthPanel, WillpowerPanel } from "./GaugePanels";
import { IdentityPanel } from "./IdentityPanel";
import { MoralityPanel, SupernaturalPanel } from "./ScalePanels";
import { StatsPanel } from "./StatsPanel";
import { TacticsPanel } from "./TacticsPanel";
import { AttributesPanel, SkillsPanel } from "./TraitPanels";

export function RectoFace() {
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
    </div>
  );
}

export function VersoFace() {
  return (
    <div className="grid grid-cols-2 items-start gap-4">
      <div className="flex flex-col gap-4">
        <EntryPanel kind="merit" />
        <EntryPanel kind="flaw" />
        <EntryPanel kind="power" />
        <TacticsPanel />
        <ExperiencePanel />
      </div>
      <div className="flex flex-col gap-4">
        <EntryPanel kind="weapon" />
        <EntryPanel kind="armor" />
        <EntryPanel kind="item" />
        <DescriptionPanel />
      </div>
    </div>
  );
}
