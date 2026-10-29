"""The tools. Every one reads only the bundled data in data/ and writes nothing."""

from __future__ import annotations

import json
import re
from pathlib import Path

from contract import (
    GameInput,
    GameOutput,
    KeyOutput,
    LettersOutput,
    ShapeCheck,
    ShapeOutput,
    WordCheck,
    WordsInput,
    WordsOutput,
)
from plugin.rules import MAX_ATTEMPTS, allowed, score, well_formed

DATA = Path(__file__).parent / "data"
GAME_NAME = re.compile(r"[a-z0-9-]+\.json")
MAX_GUESSES = 12


def words() -> frozenset[str]:
    """The allowed-words list: one lowercase 5-letter word per line, sorted, each once."""
    lines = (DATA / "words.txt").read_text(encoding="utf-8").splitlines()
    if lines != sorted(set(lines)) or not all(re.fullmatch(r"[a-z]{5}", line) for line in lines):
        raise ValueError("data/words.txt must hold sorted, distinct, lowercase 5-letter words")
    return frozenset(lines)


def load(name: str) -> GameOutput:
    """The game file ``name``, checked against the rules a game file must follow."""
    if not GAME_NAME.fullmatch(name):
        raise ValueError(f"{name!r} is not a game file name (lowercase letters, digits and '-', then .json)")
    path = DATA / "games" / name
    if not path.is_file():
        games = sorted(file.name for file in (DATA / "games").glob("*.json"))
        raise FileNotFoundError(f"no game {name!r}: the games are {', '.join(games)}")
    game = json.loads(path.read_text(encoding="utf-8"))
    if set(game) != {"answer", "max_attempts", "guesses"}:
        raise ValueError(f"{name} must hold exactly answer, max_attempts and guesses")
    answer, max_attempts, guesses = game["answer"], game["max_attempts"], game["guesses"]
    if not (isinstance(answer, str) and answer in words()):
        raise ValueError(f"{name}'s answer {answer!r} is not a lowercase word in the allowed-words list")
    if max_attempts != MAX_ATTEMPTS or isinstance(max_attempts, bool):
        raise ValueError(f"{name}'s max_attempts must be {MAX_ATTEMPTS}")
    if not (isinstance(guesses, list) and 1 <= len(guesses) <= MAX_GUESSES and all(isinstance(g, str) for g in guesses)):
        raise ValueError(f"{name}'s guesses must be 1 to {MAX_GUESSES} strings")
    return GameOutput(game=name, answer=answer, max_attempts=max_attempts, guesses=guesses)


def load_game(given: GameInput) -> KeyOutput:
    game = load(given.game)
    allowed_words = words()
    feedback, solved, attempts = score(game.answer, game.guesses, allowed_words)
    return KeyOutput(
        game=game.game,
        answer=game.answer,
        max_attempts=game.max_attempts,
        guesses=game.guesses,
        allowed=sorted(allowed_words),
        feedback=feedback,
        solved=solved,
        attempts=attempts,
    )


def read_game(given: GameInput) -> GameOutput:
    return load(given.game)


def check_words(given: WordsInput) -> WordsOutput:
    allowed_words = words()
    return WordsOutput(checks=[WordCheck(word=word, allowed=allowed(word, allowed_words)) for word in given.words])


def letters_in_word(given: GameInput) -> LettersOutput:
    return LettersOutput(letters=sorted(set(load(given.game).answer)))


def check_shape(given: WordsInput) -> ShapeOutput:
    return ShapeOutput(checks=[ShapeCheck(word=word, five_letters=well_formed(word)) for word in given.words])
