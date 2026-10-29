"""check_words: whether each word is allowed."""

from .checks import result, words_input
from .rules import ASCII_LETTERS

verify_input = words_input


def verify_output(input_value, output_value, workspace):
    if [check.word for check in output_value.checks] != input_value.words:
        return result(False, "the checks are not the words given, in order")
    for check in output_value.checks:
        if check.allowed and not (len(check.word) == 5 and all(letter in ASCII_LETTERS for letter in check.word)):
            return result(False, f"{check.word!r} is not 5 ASCII letters, so it cannot be allowed")
    return result(True, "the words are checked", allowed=sum(check.allowed for check in output_value.checks))
