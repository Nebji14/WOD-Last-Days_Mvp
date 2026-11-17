"""Dés truqués pour les tests : les faces tirées sont choisies d'avance."""


class ScriptedDice:
    """Rend les faces de ``faces`` dans l'ordre ; 5 (un échec neutre) une fois la liste vide."""

    def __init__(self) -> None:
        self.faces: list[int] = []

    def roll(self) -> int:
        return self.faces.pop(0) if self.faces else 5
