import { describe, expect, it } from "vitest";

import type { HeardMusic } from "./model";
import { parseDeck, parseNowPlaying } from "./model";
import { expectedPosition, formatDuration, needsSeek } from "./sync";

function heard(playing: boolean, position: number): HeardMusic {
  const track = { videoId: "hunt0000001", title: "La traque", channel: "N", durationSeconds: 180 };
  return {
    now: { playId: 1, track, playing, position, videoShown: false },
    receivedAt: 10_000,
  };
}

describe("position commune", () => {
  it("avance avec l'horloge pendant la lecture", () => {
    expect(expectedPosition(heard(true, 42), 15_000)).toBe(47);
  });

  it("reste fixe en pause", () => {
    expect(expectedPosition(heard(false, 42), 60_000)).toBe(42);
  });

  it("ne dépasse jamais la fin du morceau", () => {
    expect(expectedPosition(heard(true, 170), 100_000)).toBe(180);
  });

  it("ignore une horloge antérieure à la réception", () => {
    expect(expectedPosition(heard(true, 42), 9_000)).toBe(42);
  });

  it("tolère un petit écart et corrige un grand", () => {
    expect(needsSeek(41, 42)).toBe(false);
    expect(needsSeek(30, 42)).toBe(true);
    expect(needsSeek(50, 42)).toBe(true);
  });
});

describe("durée affichée", () => {
  it("suit la longueur du morceau", () => {
    expect(formatDuration(7)).toBe("0:07");
    expect(formatDuration(247)).toBe("4:07");
    expect(formatDuration(3729)).toBe("1:02:09");
  });
});

describe("données reçues", () => {
  const now = { play_id: 3, track: null, playing: false, position: 0, video_shown: false };

  it("accepte une table sans musique", () => {
    expect(parseNowPlaying(now)).toEqual({
      playId: 3,
      track: null,
      playing: false,
      position: 0,
      videoShown: false,
    });
  });

  it("refuse un état mal formé", () => {
    expect(parseNowPlaying({ ...now, track: { title: "sans identifiant" } })).toBeNull();
    expect(parseNowPlaying({ ...now, position: "0" })).toBeNull();
    expect(parseNowPlaying({ ...now, video_shown: undefined })).toBeNull();
    expect(parseDeck({ now, queue: [], repeat: "toujours" })).toBeNull();
    expect(parseDeck({ now, queue: [{ id: "a" }], repeat: "off" })).toBeNull();
  });
});
