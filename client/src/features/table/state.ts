/** État de présence de la table, tel que le diffuse le serveur. */
import { isRecord } from "@/shared/api/client";

/** Personnage joué, affiché sur le siège : visible de tous les joueurs. */
export interface SeatCharacter {
  readonly id: string;
  readonly name: string;
  readonly concept: string;
  /** Nombre de cases de santé (santé maximale effective). */
  readonly healthMax: number;
  /** Blessures, par gravité décroissante : `*` aggravée, `X` létale, `/` contondante. */
  readonly woundTrack: string;
  readonly willpowerMax: number;
  readonly willpowerCurrent: number;
  /** Nom du fichier du portrait de la forme principale, `null` sans image. */
  readonly portrait: string | null;
}

export interface Seat {
  /** Rang de la place attribuée par le serveur, de 0 à 8. */
  readonly position: number;
  readonly accountId: string;
  readonly displayName: string;
  /** `false` : le joueur a quitté la salle, son siège reste affiché atténué. */
  readonly online: boolean;
  /** `null` : le joueur n'a pas de personnage. */
  readonly character: SeatCharacter | null;
}

export interface TableState {
  readonly gm: {
    readonly displayName: string | null;
    readonly online: boolean;
    /** Nom du fichier de la photo du MJ, `null` sans photo. */
    readonly portrait: string | null;
  };
  readonly seats: readonly Seat[];
}

function parseSeatCharacter(data: unknown): SeatCharacter | null {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.name === "string" &&
    typeof data.concept === "string" &&
    typeof data.health_max === "number" &&
    typeof data.wound_track === "string" &&
    typeof data.willpower_max === "number" &&
    typeof data.willpower_current === "number"
  ) {
    return {
      id: data.id,
      name: data.name,
      concept: data.concept,
      healthMax: data.health_max,
      woundTrack: data.wound_track,
      willpowerMax: data.willpower_max,
      willpowerCurrent: data.willpower_current,
      portrait: typeof data.portrait === "string" ? data.portrait : null,
    };
  }
  return null;
}

function parseSeat(data: unknown): Seat | null {
  if (
    isRecord(data) &&
    typeof data.position === "number" &&
    typeof data.account_id === "string" &&
    typeof data.display_name === "string" &&
    typeof data.online === "boolean"
  ) {
    const character = data.character == null ? null : parseSeatCharacter(data.character);
    if (data.character != null && character === null) {
      return null;
    }
    return {
      position: data.position,
      accountId: data.account_id,
      displayName: data.display_name,
      online: data.online,
      character,
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
    gm: {
      displayName: gmName,
      online: gmOnline,
      portrait: typeof data.gm.portrait === "string" ? data.gm.portrait : null,
    },
    seats: seats.filter((seat): seat is Seat => seat !== null),
  };
}
