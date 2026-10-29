"""letters_in_word: the hidden word's distinct letters (a distractor: it drops repeated letters)."""

from .checks import game_input, result
from .rules import LOWERCASE

verify_input = game_input


def verify_output(input_value, output_value, workspace):
    letters = output_value.letters
    if not 1 <= len(letters) <= 5 or letters != sorted(set(letters)) or not all(letter in LOWERCASE for letter in letters):
        return result(False, "the letters are not 1 to 5 distinct lowercase letters, sorted")
    return result(True, "the letters are listed", letters=len(letters))
