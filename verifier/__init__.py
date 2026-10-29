"""The deterministic verifier: each tool's checks live in its own module, on contract instances."""

from contract import Task, Tool

from . import letters, load, read, shape, task, words

TOOLS = {
    Tool.LOAD_GAME: load,
    Tool.READ_GAME: read,
    Tool.CHECK_WORDS: words,
    Tool.LETTERS_IN_WORD: letters,
    Tool.CHECK_SHAPE: shape,
}
# task -> its output's check, verify_task(arguments, output, reference, workspace)
TASKS = {Task.SCORE_GAME: task.verify_task}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
