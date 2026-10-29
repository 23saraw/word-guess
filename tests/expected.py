"""Expected answers, derived by hand from the README's rules before any code ran. Never generate these.

A pattern is 5 characters: H is HIT, N is NEAR, . is MISS. I is invalid, U is unplayed."""

from __future__ import annotations

from contract import Mark, Status

GAMES = {
    # A duplicate in the guess but not the answer: only one L of LLAMA is marked; then guesses after a solve.
    "hotel.json": (
        [("llama", "N...."), ("hello", "HNN.N"), ("hotel", "HHHHH"), ("crane", "U")],
        True,
        3,
    ),
    # A duplicate in the answer but not the guess (EIGHT: one NEAR E); six wrong guesses; the answer as a 7th.
    "creep.json": (
        [
            ("eight", "N...."),
            ("geese", ".NH.."),
            ("crepe", "HHHNN"),
            ("sweep", "..HHH"),
            ("creed", "HHHH."),
            ("cheep", "H.HHH"),
            ("creep", "U"),
        ],
        False,
        6,
    ),
    # ALARM: the HIT A at position 3 uses up PLANT's one A, so the first A is MISS, not NEAR; two
    # invalid guesses that use no attempt; solved on the 6th scored guess, in uppercase; a guess after it.
    "plant.json": (
        [
            ("alarm", ".HH.."),
            ("xqzvy", "I"),
            ("plan", "I"),
            ("slant", ".HHHH"),
            ("giant", "..HHH"),
            ("blank", ".HHH."),
            ("plane", "HHHH."),
            ("PLANT", "HHHHH"),
            ("plant", "U"),
        ],
        True,
        6,
    ),
    # Mixed case; an invalid word after the solve is unplayed, not invalid.
    "crane.json": (
        [("Llama", "..H.."), ("TRACE", ".HHNH"), ("cRaNe", "HHHHH"), ("zzzzz", "U"), ("crane", "U")],
        True,
        3,
    ),
}

# (guess, answer, pattern) for the scoring rule alone.
PATTERNS = [
    ("geese", "shore", "...NH"),  # the example in the task's instructions
    ("sheep", "geese", "N.HN."),
    ("alarm", "plant", ".HH.."),
    ("llama", "hotel", "N...."),
    ("hello", "hotel", "HNN.N"),
    ("crepe", "creep", "HHHNN"),
    ("abcde", "fghij", "....."),
    ("plant", "plant", "HHHHH"),
]

MARK = {"H": Mark.HIT, "N": Mark.NEAR, ".": Mark.MISS}


def marks(pattern: str) -> list[Mark]:
    return [MARK[letter] for letter in pattern]


def feedback(game: str) -> list[dict]:
    """The game's expected feedback, as the submitted JSON gives it."""
    rows = []
    for guess, mark in GAMES[game][0]:
        if mark == "I":
            rows.append({"guess": guess, "status": Status.INVALID.value, "pattern": None})
        elif mark == "U":
            rows.append({"guess": guess, "status": Status.UNPLAYED.value, "pattern": None})
        else:
            rows.append({"guess": guess, "status": Status.SCORED.value, "pattern": [c.value for c in marks(mark)]})
    return rows


def answer(game: str) -> dict:
    """The right submission for ``game``, as JSON."""
    _, solved, attempts = GAMES[game]
    return {"game": game, "feedback": feedback(game), "solved": solved, "attempts": attempts}


def code(status: Status, pattern: list[Mark] | None) -> str:
    """A status and pattern in this file's notation: 'I', 'U' or a 5-character pattern."""
    if status is Status.INVALID:
        return "I"
    if status is Status.UNPLAYED:
        return "U"
    return "".join({value: key for key, value in MARK.items()}[mark] for mark in pattern)
