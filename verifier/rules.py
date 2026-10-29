"""The game's rules, written again apart from src/plugin/rules.py and sharing no code with it.

A wrong rule would have to be written the same wrong way twice for the answer key to pass."""

from contract import Mark, Status

MAX_ATTEMPTS = 6
MAX_GUESSES = 12
ASCII_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
LOWERCASE = frozenset("abcdefghijklmnopqrstuvwxyz")


def is_word(text):
    """Whether ``text`` is exactly 5 lowercase ASCII letters."""
    return len(text) == 5 and all(letter in LOWERCASE for letter in text)


def is_valid(guess, allowed):
    """Whether ``guess`` is 5 ASCII letters whose lowercase form is in the set ``allowed``."""
    return len(guess) == 5 and all(letter in ASCII_LETTERS for letter in guess) and guess.lower() in allowed


def marks(guess, answer):
    """The pattern of lowercase ``guess`` against ``answer``. A position that is not an exact match is NEAR
    exactly when it is among the first k such positions (left to right) holding its letter, where k is how many
    of the answer's not-exactly-matched positions hold that letter: what the two-pass rule gives."""
    exact = [guess[i] == answer[i] for i in range(5)]
    out = []
    for i in range(5):
        if exact[i]:
            out.append(Mark.HIT)
            continue
        letter = guess[i]
        seen = sum(1 for j in range(i + 1) if not exact[j] and guess[j] == letter)
        spare = sum(1 for j in range(5) if not exact[j] and answer[j] == letter)
        out.append(Mark.NEAR if seen <= spare else Mark.MISS)
    return out


def replay(answer, guesses, allowed):
    """([(status, pattern or None)] per guess, solved, attempts) for a game, under the README's rules."""
    allowed = frozenset(allowed)
    rows = []
    attempts = 0
    solved = False
    for guess in guesses:
        over = solved or attempts >= MAX_ATTEMPTS
        if over:
            rows.append((Status.UNPLAYED, None))
        elif is_valid(guess, allowed):
            attempts += 1
            rows.append((Status.SCORED, marks(guess.lower(), answer)))
            if guess.lower() == answer:
                solved = True
        else:
            rows.append((Status.INVALID, None))
    return rows, solved, attempts


def shown(pattern):
    """A pattern as words, 'MISS HIT HIT MISS MISS', or 'no pattern'."""
    return "no pattern" if pattern is None else " ".join(mark.value for mark in pattern)
