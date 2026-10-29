from __future__ import annotations

import copy
import json
import random

import pytest
from expected import GAMES, answer
from slimconfig import build_output, plain_output

import verifier
from contract import (
    GameInput,
    GameOutput,
    KeyOutput,
    LettersOutput,
    ScoreOutput,
    ShapeOutput,
    Tool,
    WordsInput,
    WordsOutput,
)
from plugin.game import check_shape, check_words, letters_in_word, load_game, read_game

IDS = ["answer-key", "answer-key-rules", "submitted-game", "patterns-shaped", "statuses", "patterns", "solved", "attempts"]


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def key_json(game: str) -> dict:
    return plain_output(load_game(GameInput(game=game)))


def judge(game: str, submitted: dict, key: dict | None = None, arguments: str | None = None) -> dict:
    reference = build_output(key_json(game) if key is None else key, KeyOutput)
    given = build_output({"game": arguments or game}, GameInput)
    return verifier.verify_task("score-game", given, build_output(submitted, ScoreOutput), reference, ".")


def failing(verdict: dict) -> list[str]:
    return [entry["id"] for entry in verdict["details"]["constraints"] if entry["ok"] is False]


def test_every_tool_resolves_to_a_module_with_both_checks() -> None:
    # The host calls verify_input and verify_output on every tool call; a missing one only fails a real run.
    assert set(verifier.TOOLS) == set(Tool)
    for module in verifier.TOOLS.values():
        assert callable(module.verify_input) and callable(module.verify_output)


@pytest.mark.parametrize("game", sorted(GAMES))
def test_the_hand_derived_answer_holds_every_constraint(game: str) -> None:
    verdict = judge(game, answer(game))
    assert verdict["valid"] is True and verdict["score"] == 1.0, verdict["message"]
    assert [entry["id"] for entry in verdict["details"]["constraints"]] == IDS
    assert verdict["message"].startswith("All 8 checks hold")


def test_the_valid_message_names_the_outcome() -> None:
    assert judge("plant.json", answer("plant.json"))["message"] == (
        "All 8 checks hold: 9 guesses (6 scored, 2 invalid, 1 unplayed), solved in 6 attempts."
    )
    assert judge("creep.json", answer("creep.json"))["message"] == (
        "All 8 checks hold: 7 guesses (6 scored, 0 invalid, 1 unplayed), not solved after 6 attempts."
    )


def test_each_tool_approves_its_own_real_output() -> None:
    game = build_output({"game": "plant.json"}, GameInput)
    words = build_output({"words": read_game(game).guesses}, WordsInput)
    cases = [
        ("load_game", game, load_game(game), KeyOutput),
        ("read_game", game, read_game(game), GameOutput),
        ("letters_in_word", game, letters_in_word(game), LettersOutput),
        ("check_words", words, check_words(words), WordsOutput),
        ("check_shape", words, check_shape(words), ShapeOutput),
    ]
    for tool, given, made, cls in cases:
        assert verifier.verify_input(tool, given)["valid"] is True, tool
        verdict = verifier.verify_output(tool, given, build_output(plain_output(made), cls), ".")
        assert verdict["valid"] is True, (tool, verdict["message"])


# Wrong answers: the traps the games are built around.
def with_entry(game: str, number: int, **changes) -> dict:
    submitted = answer(game)
    submitted["feedback"][number - 1].update(changes)
    return submitted


def test_a_one_pass_scorer_fails_patterns_on_alarm() -> None:
    verdict = judge("plant.json", with_entry("plant.json", 1, pattern=["NEAR", "HIT", "HIT", "MISS", "MISS"]))
    assert failing(verdict) == ["patterns"]
    assert verdict["message"] == (
        "patterns: guess 1 'alarm' is reported NEAR HIT HIT MISS MISS, but the rules give MISS HIT HIT MISS MISS"
    )
    assert verdict["score"] == pytest.approx(10 / 11)


def test_trusting_the_distractor_marks_both_ls_of_llama() -> None:
    verdict = judge("hotel.json", with_entry("hotel.json", 1, pattern=["NEAR", "NEAR", "MISS", "MISS", "MISS"]))
    assert failing(verdict) == ["patterns"]
    assert "guess 1 'llama' is reported NEAR NEAR MISS MISS MISS" in verdict["message"]
    assert verdict["score"] == pytest.approx(5 / 6)


def test_counting_invalid_guesses_as_attempts_fails() -> None:
    # alarm, xqzvy, plan, slant, giant, blank would be 6 attempts: plane and PLANT unplayed, not solved.
    submitted = answer("plant.json")
    for number in (2, 3):
        submitted["feedback"][number - 1].update(status="scored", pattern=["MISS"] * 5)
    for number in (7, 8):
        submitted["feedback"][number - 1].update(status="unplayed", pattern=None)
    submitted.update(solved=False, attempts=6)
    verdict = judge("plant.json", submitted)
    assert failing(verdict) == ["statuses", "solved"]
    assert verdict["message"] == (
        "statuses: guess 2 'xqzvy' is reported scored, but the rules make it invalid; also wrong: 3 more (+1 more)"
    )
    assert verdict["valid"] is False and verdict["score"] < 1


def test_scoring_a_guess_after_six_attempts_fails() -> None:
    submitted = with_entry("creep.json", 7, status="scored", pattern=["HIT"] * 5)
    submitted.update(solved=True, attempts=7)
    verdict = judge("creep.json", submitted)
    assert failing(verdict) == ["statuses", "solved", "attempts"]
    assert verdict["message"].startswith("statuses: guess 7 'creep' is reported scored, but the rules make it unplayed")


def test_an_invalid_word_after_the_solve_is_unplayed_not_invalid() -> None:
    verdict = judge("crane.json", with_entry("crane.json", 4, status="invalid"))
    assert failing(verdict) == ["statuses"]
    assert verdict["message"] == "statuses: guess 4 'zzzzz' is reported invalid, but the rules make it unplayed"


def test_solved_and_attempts_off_by_one() -> None:
    verdict = judge("hotel.json", {**answer("hotel.json"), "solved": False, "attempts": 4})
    assert failing(verdict) == ["solved", "attempts"]
    assert verdict["message"] == "solved: solved is reported False, but the rules give True (+1 more)"
    assert verdict["details"]["constraints"][7]["message"] == "attempts is reported 4, but 3 guesses are scored"
    assert verdict["score"] == pytest.approx(4 / 6)


# Missing and malformed submissions: gates that score 0.
@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda s: s.update(game="hotel.json"), "submitted-game: the submission is for 'hotel.json', not 'crane.json'"),
        (lambda s: s["feedback"].pop(), "submitted-game: 1 of the 5 guesses has no entry ('crane'): give one per guess"),
        (lambda s: s.update(feedback=[]), "submitted-game: 5 of the 5 guesses have no entry"),
        (lambda s: s["feedback"].append(dict(s["feedback"][0])), "submitted-game: the submission has 6 entries for 5 guesses"),
        (lambda s: s["feedback"][1].update(guess="trace"), "submitted-game: entry 2 is 'trace', but the game's guess 2 is 'TRACE'"),
        (lambda s: s["feedback"].reverse(), "submitted-game: entry 1 is 'crane', but the game's guess 1 is 'Llama'"),
        (lambda s: s["feedback"][0].update(pattern=["MISS"] * 4), "patterns-shaped: guess 1 'Llama' is scored with 4 marks"),
        (lambda s: s["feedback"][0].update(pattern=None), "patterns-shaped: guess 1 'Llama' is scored with no marks"),
        (lambda s: s["feedback"][3].update(pattern=["MISS"] * 5), "patterns-shaped: guess 4 'zzzzz' is unplayed but has a pattern"),
    ],
)
def test_a_malformed_submission_fails_its_gate_and_scores_zero(change, message: str) -> None:
    submitted = copy.deepcopy(answer("crane.json"))
    change(submitted)
    verdict = judge("crane.json", submitted)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["message"].startswith(message), verdict["message"]
    later = verdict["details"]["constraints"][IDS.index(failing(verdict)[0]) + 1 :]
    assert all(entry["ok"] is None and entry["message"].startswith("Not checked") for entry in later)


def test_a_mark_outside_the_enum_never_reaches_the_verifier() -> None:
    # Unreachable in verify_task: build_output checks the contract's Mark Enum first, as the sandbox does.
    submitted = with_entry("hotel.json", 1, pattern=["BLUE", "MISS", "MISS", "MISS", "MISS"])
    with pytest.raises((TypeError, ValueError)):
        build_output(submitted, ScoreOutput)


# The answer key.
def test_no_answer_key_fails_first() -> None:
    given = build_output({"game": "hotel.json"}, GameInput)
    verdict = verifier.verify_task("score-game", given, build_output(answer("hotel.json"), ScoreOutput), None, ".")
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["message"] == "answer-key: No answer key: load_game never ran for this task."


def test_an_answer_key_for_another_game_fails() -> None:
    verdict = judge("hotel.json", answer("hotel.json"), arguments="crane.json")
    assert verdict["message"] == "answer-key: The answer key is for 'hotel.json', not 'crane.json'."


def test_an_answer_key_with_a_word_outside_its_list_fails() -> None:
    key = key_json("hotel.json")
    key["allowed"].remove("hotel")
    verdict = judge("hotel.json", answer("hotel.json"), key=key)
    assert verdict["message"] == "answer-key: the answer 'hotel' is not in the allowed-words list"


def test_a_tampered_answer_key_fails_its_rules_check() -> None:
    key = key_json("hotel.json")
    key["feedback"][0]["pattern"] = ["NEAR", "NEAR", "MISS", "MISS", "MISS"]
    verdict = judge("hotel.json", answer("hotel.json"), key=key)
    assert failing(verdict) == ["answer-key-rules"]
    assert verdict["message"] == "answer-key-rules: the answer key's guess 1 'llama' breaks the rules"
    output = verifier.verify_output("load_game", build_output({"game": "hotel.json"}, GameInput), build_output(key, KeyOutput), ".")
    assert output["valid"] is False


# The tools' own checks.
def test_tool_inputs_are_checked() -> None:
    assert verifier.verify_input("read_game", build_output({"game": "../words.txt"}, GameInput))["valid"] is False
    assert verifier.verify_input("check_words", build_output({"words": []}, WordsInput))["valid"] is False


@pytest.mark.parametrize(
    ("tool", "given", "made", "cls"),
    [
        ("check_words", {"words": ["plan"]}, {"checks": [{"word": "plan", "allowed": True}]}, WordsOutput),
        ("check_words", {"words": ["plan"]}, {"checks": []}, WordsOutput),
        ("check_shape", {"words": ["plan"]}, {"checks": [{"word": "plan", "five_letters": True}]}, ShapeOutput),
        ("letters_in_word", {"game": "creep.json"}, {"letters": ["c", "e", "e", "p", "r"]}, LettersOutput),
        ("letters_in_word", {"game": "creep.json"}, {"letters": ["r", "p", "e", "c"]}, LettersOutput),
        ("read_game", {"game": "creep.json"}, {"game": "creep.json", "answer": "creep", "max_attempts": 5, "guesses": ["eight"]}, GameOutput),
        ("read_game", {"game": "creep.json"}, {"game": "hotel.json", "answer": "hotel", "max_attempts": 6, "guesses": ["eight"]}, GameOutput),
    ],
)
def test_a_wrong_tool_output_is_refused(tool: str, given: dict, made: dict, cls: type) -> None:
    input_class = GameInput if "game" in given else WordsInput
    verdict = verifier.verify_output(tool, build_output(given, input_class), build_output(made, cls), ".")
    assert verdict["valid"] is False


# Determinism, size and robustness.
def test_the_verdict_is_deterministic_and_small() -> None:
    submitted = with_entry("plant.json", 1, pattern=["NEAR", "HIT", "HIT", "MISS", "MISS"])
    first, second = judge("plant.json", submitted), judge("plant.json", submitted)
    assert first == second
    assert len(json.dumps(first)) < 8_000


def mutate(value, rng: random.Random):
    """``value`` with one random change somewhere inside it."""
    if isinstance(value, dict) and value:
        key = rng.choice(sorted(value))
        return {**value, key: mutate(value[key], rng)}
    if isinstance(value, list) and value and rng.random() < 0.7:
        index = rng.randrange(len(value))
        choice = rng.random()
        if choice < 0.3:
            return value[:index] + value[index + 1 :]
        if choice < 0.5:
            return [*value, copy.deepcopy(value[index])]
        return value[:index] + [mutate(value[index], rng)] + value[index + 1 :]
    # Mostly a value of the same type, so most mutations reach the verifier rather than build_output's refusal.
    same = {
        bool: [True, False],
        int: [0, -1, 1, 6, 7, 99],
        str: ["", "HIT", "NEAR", "MISS", "scored", "invalid", "unplayed", "plant", "PLANT", "hotel.json", "Knife"],
        list: [[], ["MISS"] * 5, ["HIT"] * 6],
    }.get(type(value))
    if same and rng.random() < 0.85:
        return rng.choice(same)
    return rng.choice([None, "", 0, True, [], ["MISS"] * 5])


@pytest.mark.parametrize("game", sorted(GAMES))
def test_a_mutated_submission_or_key_always_gets_a_verdict(game: str) -> None:
    rng = random.Random(game)
    checked = 0
    for _ in range(300):
        submitted, key = answer(game), key_json(game)
        for _ in range(rng.randint(1, 3)):
            if rng.random() < 0.7:
                submitted = mutate(submitted, rng)
            else:
                key = mutate(key, rng)
        try:
            built_output, built_key = build_output(submitted, ScoreOutput), build_output(key, KeyOutput)
        except (TypeError, ValueError, KeyError):
            continue  # the sandbox refuses it before the verifier sees it
        given = build_output({"game": game}, GameInput)
        verdict = verifier.verify_task("score-game", given, built_output, built_key, ".")
        assert set(verdict) == {"valid", "score", "message", "details"}
        assert 0.0 <= verdict["score"] <= 1.0 and verdict["message"]
        json.dumps(verdict)
        checked += 1
    assert checked > 150
