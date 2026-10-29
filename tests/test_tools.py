from __future__ import annotations

import pytest

from contract import GameInput, WordsInput
from plugin import game as game_module
from plugin.game import check_shape, check_words, letters_in_word, load_game, read_game


def test_read_game_gives_the_game_as_written() -> None:
    game = read_game(GameInput(game="crane.json"))
    assert (game.answer, game.max_attempts) == ("crane", 6)
    assert game.guesses == ["Llama", "TRACE", "cRaNe", "zzzzz", "crane"]


def test_the_answer_key_and_read_game_agree() -> None:
    key = load_game(GameInput(game="plant.json"))
    game = read_game(GameInput(game="plant.json"))
    assert (key.game, key.answer, key.max_attempts, key.guesses) == (game.game, game.answer, game.max_attempts, game.guesses)
    assert key.allowed == sorted(set(key.allowed)) and "plant" in key.allowed


def test_check_words_reads_the_list_and_check_shape_does_not() -> None:
    words = ["PLANT", "xqzvy", "plan", " crane"]
    assert [check.allowed for check in check_words(WordsInput(words=words)).checks] == [True, False, False, False]
    assert [check.five_letters for check in check_shape(WordsInput(words=words)).checks] == [True, True, False, False]


def test_letters_in_word_drops_repeats() -> None:
    assert letters_in_word(GameInput(game="creep.json")).letters == ["c", "e", "p", "r"]


@pytest.mark.parametrize(("name", "error"), [("../words.txt", ValueError), ("Hotel.json", ValueError), ("nope.json", FileNotFoundError)])
def test_a_bad_game_name_raises(name: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        read_game(GameInput(game=name))


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ('{"answer": "plant", "max_attempts": 5, "guesses": ["crane"]}', "max_attempts"),
        ('{"answer": "plant", "max_attempts": true, "guesses": ["crane"]}', "max_attempts"),
        ('{"answer": "PLANT", "max_attempts": 6, "guesses": ["crane"]}', "answer"),
        ('{"answer": "xqzvy", "max_attempts": 6, "guesses": ["crane"]}', "answer"),
        ('{"answer": "plant", "max_attempts": 6, "guesses": []}', "guesses"),
        ('{"answer": "plant", "max_attempts": 6, "guesses": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]}', "guesses"),
        ('{"answer": "plant", "max_attempts": 6, "guesses": [5]}', "guesses"),
        ('{"answer": "plant", "max_attempts": 6, "guesses": ["crane"], "hint": "p"}', "exactly"),
    ],
)
def test_a_bad_game_file_raises(tmp_path, monkeypatch, content: str, match: str) -> None:
    (tmp_path / "games").mkdir()
    (tmp_path / "games" / "bad.json").write_text(content)
    (tmp_path / "words.txt").write_text((game_module.DATA / "words.txt").read_text())
    monkeypatch.setattr(game_module, "DATA", tmp_path)
    with pytest.raises(ValueError, match=match):
        read_game(GameInput(game="bad.json"))
