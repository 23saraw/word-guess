"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output

GAME = "A bundled game file's name, such as 'hotel.json'"
GUESSES = "The game's guesses, in order, exactly as written in the game file"


class Tool(Enum):
    LOAD_GAME = "load_game"
    READ_GAME = "read_game"
    CHECK_WORDS = "check_words"
    LETTERS_IN_WORD = "letters_in_word"
    CHECK_SHAPE = "check_shape"


class Task(Enum):
    SCORE_GAME = "score-game"


class Mark(Enum):
    HIT = "HIT"
    NEAR = "NEAR"
    MISS = "MISS"


class Status(Enum):
    SCORED = "scored"
    INVALID = "invalid"
    UNPLAYED = "unplayed"


@dataclass
class GameInput(Output):
    game: Annotated[str, GAME]


@dataclass
class GameOutput(Output):
    game: Annotated[str, GAME]
    answer: Annotated[str, "The hidden word: 5 lowercase letters, in the allowed-words list"]
    max_attempts: Annotated[int, "The most scored guesses the game allows: always 6"]
    guesses: Annotated[list[str], GUESSES]


@dataclass
class WordsInput(Output):
    words: Annotated[list[str], "The words to check, exactly as written"]


@dataclass
class WordCheck(Output):
    word: Annotated[str, "The word, as given"]
    allowed: Annotated[bool, "Whether the word is 5 ASCII letters and, lowercased, in the allowed-words list"]


@dataclass
class WordsOutput(Output):
    checks: Annotated[list[WordCheck], "One check per word, in the order given"]


@dataclass
class LettersOutput(Output):
    letters: Annotated[list[str], "The distinct letters of the hidden word, sorted, each listed once"]


@dataclass
class ShapeCheck(Output):
    word: Annotated[str, "The word, as given"]
    five_letters: Annotated[bool, "Whether the word is exactly 5 ASCII letters; the allowed-words list is not read"]


@dataclass
class ShapeOutput(Output):
    checks: Annotated[list[ShapeCheck], "One check per word, in the order given"]


@dataclass
class Feedback(Output):
    guess: Annotated[str, "The guess, exactly as written in the game file"]
    status: Annotated[
        Status,
        "scored: an allowed guess played while the game is on; invalid: not allowed, uses no attempt;"
        " unplayed: any guess after the game is over",
    ]
    pattern: Annotated[
        list[Mark] | None,
        "The 5 marks of a scored guess, left to right (HIT: right letter, right position; NEAR: in the word, not"
        " here, with an unused copy remaining; MISS: otherwise); null otherwise",
    ]


@dataclass
class ScoreOutput(Output):
    game: Annotated[str, GAME]
    feedback: Annotated[list[Feedback], "One entry per guess, in the game file's order"]
    solved: Annotated[bool, "Whether a scored guess equals the hidden word"]
    attempts: Annotated[int, "How many guesses are scored"]


@dataclass
class KeyOutput(Output):
    game: Annotated[str, GAME]
    answer: Annotated[str, "The hidden word"]
    max_attempts: Annotated[int, "The most scored guesses the game allows"]
    guesses: Annotated[list[str], GUESSES]
    allowed: Annotated[list[str], "The allowed-words list: lowercase, sorted, each word once"]
    feedback: Annotated[list[Feedback], "Each guess's expected feedback"]
    solved: Annotated[bool, "Whether the game is expected to be solved"]
    attempts: Annotated[int, "The expected number of scored guesses"]


TOOLS = {
    Tool.LOAD_GAME: (GameInput, KeyOutput),
    Tool.READ_GAME: (GameInput, GameOutput),
    Tool.CHECK_WORDS: (WordsInput, WordsOutput),
    Tool.LETTERS_IN_WORD: (GameInput, LettersOutput),
    Tool.CHECK_SHAPE: (WordsInput, ShapeOutput),
}
TASKS = {Task.SCORE_GAME: (GameInput, ScoreOutput)}
