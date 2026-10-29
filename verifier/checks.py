"""Checks shared by the tool verifiers. Pure functions of their arguments."""

import re

from .rules import MAX_ATTEMPTS, MAX_GUESSES, is_word, replay

GAME_NAME = re.compile(r"[a-z0-9-]+\.json")
MAX_WORDS = 50  # words one check_words or check_shape call may take
MOST = 6  # list entries a constraint's expected or actual shows


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def constraint(identifier, text, ok, expected=None, actual=None, message=""):
    """One constraint's entry, always with the same keys: ok is True (holds), False (fails) or None (not
    checked: a check it needs did not hold); message says why it fails or was not checked, "" when it holds."""
    def cut(value):
        return value[:MOST] + [f"... {len(value) - MOST} more"] if isinstance(value, list) and len(value) > MOST else value

    return {
        "id": identifier,
        "constraint": text,
        "ok": ok,
        "expected": cut(expected),
        "actual": cut(actual),
        "message": "" if ok is True else message or text,
    }


def summary(constraints):
    """A failed verdict's message: the first failing constraint, its id and why, then how many more fail."""
    failed = [entry for entry in constraints if entry["ok"] is False]
    first = failed[0]
    more = f" (+{len(failed) - 1} more)" if len(failed) > 1 else ""
    return f"{first['id']}: {first['message']}{more}"


def game_input(value):
    if not GAME_NAME.fullmatch(value.game):
        return result(False, f"{value.game!r} is not a game file name (lowercase letters, digits and '-', then .json)")
    return result(True, "input is valid")


def words_input(value):
    if not 1 <= len(value.words) <= MAX_WORDS:
        return result(False, f"give 1 to {MAX_WORDS} words, not {len(value.words)}")
    return result(True, "input is valid")


def game_problem(game, answer, max_attempts, guesses):
    """What is wrong with a game as a tool gives it, or None. The allowed-words list is not known here."""
    if not GAME_NAME.fullmatch(game):
        return f"{game!r} is not a game file name"
    if not is_word(answer):
        return f"the answer {answer!r} is not 5 lowercase letters"
    if max_attempts != MAX_ATTEMPTS:
        return f"max_attempts is {max_attempts}, not {MAX_ATTEMPTS}"
    if not 1 <= len(guesses) <= MAX_GUESSES:
        return f"the game has {len(guesses)} guesses, not 1 to {MAX_GUESSES}"
    return None


def key_problem(key):
    """What is wrong with the answer key's data, or None: its game, its allowed-words list and its feedback's
    guesses (not yet whether its feedback follows the rules)."""
    problem = game_problem(key.game, key.answer, key.max_attempts, key.guesses)
    if problem:
        return problem
    if not key.allowed or key.allowed != sorted(set(key.allowed)) or not all(is_word(word) for word in key.allowed):
        return "the allowed-words list is not sorted, distinct, lowercase 5-letter words"
    if key.answer not in key.allowed:
        return f"the answer {key.answer!r} is not in the allowed-words list"
    if [entry.guess for entry in key.feedback] != key.guesses:
        return "the answer key's feedback does not list the game's guesses, in order"
    return None


def key_rules_problem(key):
    """Where the answer key's feedback, solved or attempts differ from the rules, or None (key_problem holds)."""
    rows, solved, attempts = replay(key.answer, key.guesses, key.allowed)
    for number, (entry, (status, pattern)) in enumerate(zip(key.feedback, rows), 1):
        if (entry.status, entry.pattern) != (status, pattern):
            return f"the answer key's guess {number} {entry.guess!r} breaks the rules"
    if (key.solved, key.attempts) != (solved, attempts):
        return f"the answer key says solved {key.solved} in {key.attempts}, the rules give solved {solved} in {attempts}"
    return None

