import { describe, expect, it } from "vitest";

import { buildSuggestions, isLink, matches, withRecent } from "./suggestions";

const sources = {
  recent: ["Hans Zimmer - Time"],
  ambiances: ["musique de combat épique", "ambiance taverne"],
  playlistTitles: ["Épée du chasseur"],
  remote: { query: "hans", items: ["Hans Zimmer", "Hans Zimmer - Time", "Nana"] },
};

describe("correspondance", () => {
  it("accepte un mot incomplet, sans accent ni majuscule", () => {
    expect(matches("musique de combat épique", "COMB epi")).toBe(true);
    expect(matches("ambiance taverne", "averne")).toBe(false);
  });

  it("reconnaît un lien", () => {
    expect(isLink("https://youtu.be/abc")).toBe(true);
    expect(isLink("youtube.com/watch?v=abc")).toBe(true);
    expect(isLink("musique youtube")).toBe(false);
  });
});

describe("suggestions", () => {
  it("mélange récentes et noms du serveur, sans doublon", () => {
    expect(buildSuggestions("hans", sources)).toEqual([
      "Hans Zimmer - Time",
      "Hans Zimmer",
      "Nana",
    ]);
  });

  it("garde la réponse précédente tant qu'elle correspond", () => {
    expect(buildSuggestions("hans zim", sources)).toEqual(["Hans Zimmer - Time", "Hans Zimmer"]);
  });

  it("propose les ambiances et les morceaux des playlists", () => {
    expect(buildSuggestions("epee", sources)).toEqual(["Épée du chasseur"]);
    expect(buildSuggestions("taver", sources)).toEqual(["ambiance taverne"]);
  });

  it("montre les récentes et les ambiances quand le champ est vide", () => {
    expect(buildSuggestions("", sources)[0]).toBe("Hans Zimmer - Time");
    expect(buildSuggestions("", sources)).toHaveLength(3);
  });

  it("ne répète pas le texte déjà saisi et ignore les liens", () => {
    expect(buildSuggestions("Ambiance Taverne", sources)).toEqual([]);
    expect(buildSuggestions("https://youtu.be/abc", sources)).toEqual([]);
  });

  it("remonte une recherche refaite", () => {
    expect(withRecent(["a", "b"], "B")).toEqual(["B", "a"]);
  });
});
