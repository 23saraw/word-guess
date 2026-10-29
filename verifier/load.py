"""load_game: the score-game answer key."""

from .checks import game_input, key_problem, key_rules_problem, result

verify_input = game_input


def verify_output(input_value, output_value, workspace):
    if output_value.game != input_value.game:
        return result(False, f"the answer key is for {output_value.game!r}, not {input_value.game!r}")
    problem = key_problem(output_value) or key_rules_problem(output_value)
    if problem:
        return result(False, problem)
    return result(True, "the answer key follows the rules", guesses=len(output_value.guesses))
