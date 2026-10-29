"""Both implementations of the rules (the plugin's and the verifier's) against the hand-derived answers."""

from __future__ import annotations

import pytest
from expected import GAMES, PATTERNS, code, marks

from contract import Status
from plugin import rules as plugin_rules
from plugin.game import load, words
from verifier import rules as verifier_rules


@pytest.mark.parametrize(("guess", "answer", "pattern"), PATTERNS)
def test_both_score_a_guess_by_the_two_pass_rule(guess: str, answer: str, pattern: str) -> None:
    assert plugin_rules.pattern(guess, answer) == marks(pattern)
    assert verifier_rules.marks(guess, answer) == marks(pattern)


@pytest.mark.parametrize("name", sorted(GAMES))
def test_both_referee_each_game_as_derived_by_hand(name: str) -> None:
    game = load(name)
    rows, solved, attempts = GAMES[name]
    feedback, plugin_solved, plugin_attempts = plugin_rules.score(game.answer, game.guesses, words())
    assert [(entry.guess, code(entry.status, entry.pattern)) for entry in feedback] == rows
    assert (plugin_solved, plugin_attempts) == (solved, attempts)
    replayed, verifier_solved, verifier_attempts = verifier_rules.replay(game.answer, game.guesses, sorted(words()))
    assert [(guess, code(*row)) for guess, row in zip(game.guesses, replayed)] == rows
    assert (verifier_solved, verifier_attempts) == (solved, attempts)


@pytest.mark.parametrize(
    "guess",
    [
        " crane",  # not stripped
        "crane ",
        "cran",
        "cranes",
        "",
        "cr4ne",
        "Knife",  # KELVIN SIGN: str.lower() makes it 'knife', but it is not an ASCII letter
        "cráne",
        "xqzvy",  # five letters, not in the list
    ],
)
def test_both_call_a_malformed_or_unlisted_guess_invalid(guess: str) -> None:
    allowed = words()
    assert plugin_rules.allowed(guess, allowed) is False
    assert verifier_rules.is_valid(guess, allowed) is False


def test_both_accept_any_case_of_an_allowed_word() -> None:
    for guess in ("knife", "KNIFE", "kNiFe"):
        assert plugin_rules.allowed(guess, words()) is True
        assert verifier_rules.is_valid(guess, words()) is True


def test_a_repeated_guess_scores_again_and_uses_an_attempt() -> None:
    allowed = words()
    guesses = ["crane"] * 7
    feedback, solved, attempts = plugin_rules.score("plant", guesses, allowed)
    assert [entry.status for entry in feedback] == [Status.SCORED] * 6 + [Status.UNPLAYED]
    assert (solved, attempts) == (False, 6)
    rows, solved, attempts = verifier_rules.replay("plant", guesses, allowed)
    assert [status for status, _ in rows] == [Status.SCORED] * 6 + [Status.UNPLAYED]
    assert (solved, attempts) == (False, 6)
