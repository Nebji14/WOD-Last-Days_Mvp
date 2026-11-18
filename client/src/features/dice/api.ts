/** Appels API des jets de dés. */
import { ApiError, apiRequest } from "@/shared/api/client";

import { parseRoll, type Roll, type RollKind } from "./model";

export interface RollRequest {
  readonly kind: RollKind;
  readonly character_id?: string;
  readonly sheet_id?: string;
  readonly attribute?: string;
  readonly second?: string;
  readonly trait?: string;
  readonly dice?: number;
  readonly entry_id?: string;
  readonly specialty?: boolean;
  readonly willpower?: boolean;
  readonly modifier?: number;
  readonly again?: number;
  readonly rote?: boolean;
  readonly secret?: boolean;
}

function parse(data: unknown): Roll {
  const roll = parseRoll(data);
  if (roll === null) {
    throw new ApiError(502, "internal_error");
  }
  return roll;
}

/** Lance un jet : le serveur tire les dés et les montre à toute la table. */
export function startRoll(request: RollRequest): Promise<Roll> {
  return apiRequest("/api/dice/rolls", { method: "POST", body: request, parse });
}

/** Relance les dés en attente d'un jet que l'on a lancé. */
export function rerollDice(rollId: string): Promise<Roll> {
  return apiRequest(`/api/dice/rolls/${rollId}/reroll`, { method: "POST", parse });
}
