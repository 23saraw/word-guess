"""read_game: the game the agent referees."""

from .checks import game_input, game_problem, result

verify_input = game_input


def verify_output(input_value, output_value, workspace):
    if output_value.game != input_value.game:
        return result(False, f"read_game gave {output_value.game!r}, not {input_value.game!r}")
    problem = game_problem(output_value.game, output_value.answer, output_value.max_attempts, output_value.guesses)
    if problem:
        return result(False, problem)
    return result(True, "the game is read", guesses=len(output_value.guesses))
