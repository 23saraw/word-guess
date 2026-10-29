"""The game's rules, as the README pins them. load_game's answer key is computed here."""

from __future__ import annotations

import re
from collections import Counter

from contract import Feedback, Mark, Status

MAX_ATTEMPTS = 6
WORD = re.compile(r"[A-Za-z]{5}")  # exactly 5 ASCII letters, before lowercasing


def well_formed(word: str) -> bool:
    return WORD.fullmatch(word) is not None


def allowed(word: str, words: frozenset[str]) -> bool:
    """Whether ``word`` is 5 ASCII letters and, lowercased, in ``words``."""
    return well_formed(word) and word.lower() in words


def pattern(guess: str, answer: str) -> list[Mark]:
    """Two passes: exact matches are HIT and use up their letter; then, left to right, a letter is NEAR
    while the answer still has an unused copy of it, else MISS."""
    marks = [Mark.HIT if g == a else None for g, a in zip(guess, answer)]
    unused = Counter(a for a, mark in zip(answer, marks) if mark is None)
    for i, letter in enumerate(guess):
        if marks[i] is None:
            marks[i] = Mark.NEAR if unused[letter] else Mark.MISS
            unused[letter] -= bool(unused[letter])
    return marks


def score(answer: str, guesses: list[str], words: frozenset[str]) -> tuple[list[Feedback], bool, int]:
    """Each guess's feedback, whether the game is solved, and how many guesses are scored."""
    feedback: list[Feedback] = []
    solved, attempts = False, 0
    for guess in guesses:
        if solved or attempts == MAX_ATTEMPTS:
            feedback.append(Feedback(guess=guess, status=Status.UNPLAYED, pattern=None))
        elif not allowed(guess, words):
            feedback.append(Feedback(guess=guess, status=Status.INVALID, pattern=None))
        else:
            word = guess.lower()
            attempts += 1
            solved = word == answer
            feedback.append(Feedback(guess=guess, status=Status.SCORED, pattern=pattern(word, answer)))
    return feedback, solved, attempts
