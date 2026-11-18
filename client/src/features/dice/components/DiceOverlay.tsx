"use client";

/**
 * Jets de dés joués devant toute la table, l'un après l'autre.
 *
 * Chaque vague roule sur la table puis vient en gros plan, réussites en
 * lumière. S'il reste des dés à relancer, le lanceur clique « Relancer » (son
 * écran relance seul après quelques secondes) ; les autres voient l'attente. Le
 * résultat reste affiché quelques secondes, puis le jet passe dans le chat.
 */
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { fill, labels } from "@/shared/i18n";

import { rerollDice } from "../api";
import { describeParts, resultLabel, successesLabel } from "../format";
import { isSuccess, type Roll } from "../model";
import { useDiceStore } from "../store";
import type { DieStyle } from "../three/materials";

const DiceScene = dynamic(() => import("../three/DiceScene"), { ssr: false });

/** Temps laissé au résultat final avant qu'il ne passe dans le chat. */
const FINAL_HOLD_MS = 4500;

const OUTCOME_STYLE: Record<string, string> = {
  exceptional: "text-gold drop-shadow-[0_0_18px_rgb(201_176_106/0.8)]",
  success: "text-copper-light",
  failure: "text-ink-muted",
  dramatic_failure: "text-danger-bright drop-shadow-[0_0_14px_rgb(232_87_74/0.7)]",
};

/** Délai avant que l'écran du lanceur relance de lui-même. */
const AUTO_REROLL_MS = 6000;

function RerollAction({ roll, isRoller }: { roll: Roll; isRoller: boolean }) {
  const [sending, setSending] = useState(false);
  const text = labels.dice;

  // Le délai court à partir du moment où ses dés passent à l'écran, même si
  // d'autres jets sont passés avant.
  useEffect(() => {
    if (!isRoller) {
      return;
    }
    const timer = window.setTimeout(() => {
      setSending(true);
      rerollDice(roll.id).catch(() => setSending(false));
    }, AUTO_REROLL_MS);
    return () => window.clearTimeout(timer);
  }, [isRoller, roll.id]);

  if (!isRoller) {
    return (
      <p className="text-ink-muted text-lg italic">
        {fill(text.rerollWaiting, { name: roll.roller_name, count: roll.pending })}
      </p>
    );
  }
  return (
    <div className="flex flex-col items-center gap-1.5">
      <button
        type="button"
        disabled={sending}
        onClick={() => {
          setSending(true);
          rerollDice(roll.id).catch(() => setSending(false));
        }}
        className="font-display pointer-events-auto cursor-pointer rounded-xs border border-[#D8352C] bg-gradient-to-b from-[#B3261F] to-[#7A1512] px-6 py-3 text-sm font-bold tracking-[3px] text-white shadow-[0_0_24px_rgb(179_38_31/0.6)] hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
      >
        {roll.pending === 1 ? text.rerollOne : fill(text.rerollButton, { count: roll.pending })}
      </button>
      <span className="text-ink-muted text-sm italic">{text.rerollAuto}</span>
    </div>
  );
}

function RollPlayer({ roll, viewerId }: { roll: Roll; viewerId: string }) {
  const done = useDiceStore((state) => state.done);
  const [thrown, setThrown] = useState(0);
  const style: DieStyle = roll.roller_role === "gm" ? "gm" : "player";
  const throwing = thrown < roll.stages.length;
  const final = !throwing && roll.pending === 0;

  useEffect(() => {
    if (!final) {
      return;
    }
    const timer = window.setTimeout(() => done(roll.id), FINAL_HOLD_MS);
    return () => window.clearTimeout(timer);
  }, [final, done, roll.id]);

  const throwSpec = throwing
    ? { key: `${roll.id}:${thrown}`, values: roll.stages[thrown] ?? [], style }
    : null;
  const closeup = throwing
    ? null
    : {
        key: `${roll.id}:closeup:${roll.stages.length}`,
        style,
        dice: roll.stages.flatMap((faces, stage) =>
          faces.map((value) => ({
            value,
            success: roll.kind === "initiative" || isSuccess(value, roll.chance),
            fresh: stage === roll.stages.length - 1,
          })),
        ),
      };

  return (
    <div className="pointer-events-none fixed inset-0 z-[60] flex flex-col">
      {/* Au gros plan, la table s'efface derrière les dés pour que le résultat se lise. */}
      <div
        aria-hidden="true"
        className={`animate-fade-to-black absolute inset-0 transition-[background-color,backdrop-filter] duration-500 ${
          throwing ? "bg-black/50" : "bg-black/80 backdrop-blur-md"
        }`}
      />
      <div className="absolute inset-0">
        <DiceScene
          throwSpec={throwSpec}
          closeup={closeup}
          onThrowEnd={() => setThrown((count) => count + 1)}
        />
      </div>
      <header className="relative mt-10 flex flex-col items-center gap-1 text-center">
        <p className="font-display text-gold text-sm font-bold tracking-[4px]">
          {fill(labels.dice.rolledBy, { name: roll.roller_name })}
          {roll.secret && (
            <span className="border-gold ml-3 rounded-xs border px-2 py-0.5 text-[10px]">
              {labels.dice.secretBadge}
            </span>
          )}
        </p>
        <p className="text-ink text-xl italic">
          {roll.chance ? labels.dice.chanceDie : describeParts(roll.parts)}
        </p>
      </header>
      {!throwing && (
        <footer
          role="status"
          className="relative mt-auto mb-12 flex flex-col items-center gap-3 text-center"
        >
          <p
            className={`font-display rounded-md border border-white/10 bg-black/70 px-10 py-4 text-6xl font-black tracking-[5px] shadow-[0_0_40px_rgb(0_0_0/0.9)] [text-shadow:0_3px_10px_rgb(0_0_0/0.95)] ${
              final ? (OUTCOME_STYLE[roll.outcome ?? "success"] ?? "") : "text-ink-bright"
            }`}
          >
            {final ? resultLabel(roll) : successesLabel(roll.successes)}
          </p>
          {final && roll.total === null && roll.outcome !== "failure" && (
            <p className="text-ink-bright text-3xl font-bold [text-shadow:0_2px_8px_rgb(0_0_0/0.95)]">
              {successesLabel(roll.successes)}
            </p>
          )}
          {!final && (
            <RerollAction
              key={roll.stages.length}
              roll={roll}
              isRoller={roll.roller_id === viewerId}
            />
          )}
        </footer>
      )}
    </div>
  );
}

/** Le jet en tête de file, s'il y en a un. */
export function DiceOverlay({ viewerId }: { viewerId: string }) {
  const current = useDiceStore((state) => state.queue[0] ?? null);
  return current === null ? null : (
    <RollPlayer key={current.id} roll={current} viewerId={viewerId} />
  );
}
