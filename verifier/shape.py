"""check_shape: whether each word is 5 ASCII letters (a distractor: it never reads the allowed-words list)."""

from .checks import result, words_input
from .rules import ASCII_LETTERS

verify_input = words_input


def verify_output(input_value, output_value, workspace):
    if [check.word for check in output_value.checks] != input_value.words:
        return result(False, "the checks are not the words given, in order")
    for check in output_value.checks:
        if check.five_letters != (len(check.word) == 5 and all(letter in ASCII_LETTERS for letter in check.word)):
            return result(False, f"{check.word!r} is reported five_letters {check.five_letters}, which is wrong")
    return result(True, "the words are checked")
