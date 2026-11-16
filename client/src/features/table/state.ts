/** État de présence de la table, tel que le diffuse le serveur (US-012 · CA2, US-028 · CA1). */
import { isRecord } from "@/shared/api/client";

export interface Seat {
  /** Rang de la place attribuée par le serveur, de 0 à 8. */
  readonly position: number;
  readonly accountId: string;
  readonly displayName: string;
  /** `false` : le joueur a quitté la salle, son siège reste affiché atténué (03-E2). */
  readonly online: boolean;
}

export interface TableState {
  readonly gm: { readonly displayName: string | null; readonly online: boolean };
  readonly seats: readonly Seat[];
}

function parseSeat(data: unknown): Seat | null {
  if (
    isRecord(data) &&
    typeof data.position === "number" &&
    typeof data.account_id === "string" &&
    typeof data.display_name === "string" &&
    typeof data.online === "boolean"
  ) {
    return {
      position: data.position,
      accountId: data.account_id,
      displayName: data.display_name,
      online: data.online,
    };
  }
  return null;
}

/** Valide un événement `table.state`. Retourne `null` s'il est mal formé. */
export function parseTableState(data: unknown): TableState | null {
  if (!isRecord(data) || !isRecord(data.gm) || !Array.isArray(data.seats)) {
    return null;
  }
  const { display_name: gmName, online: gmOnline } = data.gm;
  const seats = data.seats.map(parseSeat);
  if (
    (gmName !== null && typeof gmName !== "string") ||
    typeof gmOnline !== "boolean" ||
    seats.some((seat) => seat === null)
  ) {
    return null;
  }
  return {
    gm: { displayName: gmName, online: gmOnline },
    seats: seats.filter((seat): seat is Seat => seat !== null),
  };
}
