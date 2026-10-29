"""The score-game task's verdict: 8 named constraints, in order. 1 to 4 guard the answer key and the
submission's integrity and score 0 when one fails; 5 to 8 judge the answer and score partially."""

from contract import Status

from .checks import constraint, key_problem, key_rules_problem, result, summary
from .rules import replay, shown

GATES = 4


def _numbered(number, guess):
    return f"guess {number} {guess!r}"


def _submitted_game(arguments, output, key):
    if output.game != arguments.game:
        return f"the submission is for {output.game!r}, not {arguments.game!r}"
    given = [entry.guess for entry in output.feedback]
    if len(given) < len(key.guesses):
        missing = ", ".join(repr(guess) for guess in key.guesses[len(given):])
        count = len(key.guesses) - len(given)
        verb = "has" if count == 1 else "have"
        return f"{count} of the {len(key.guesses)} guesses {verb} no entry ({missing}): give one per guess"
    if len(given) > len(key.guesses):
        return f"the submission has {len(given)} entries for {len(key.guesses)} guesses: give exactly one per guess"
    for number, (ours, theirs) in enumerate(zip(given, key.guesses), 1):
        if ours != theirs:
            return f"entry {number} is {ours!r}, but the game's guess {number} is {theirs!r}: copy each guess exactly as written"
    return None


def _patterns_shaped(output):
    for number, entry in enumerate(output.feedback, 1):
        name = _numbered(number, entry.guess)
        if entry.status is Status.SCORED and (entry.pattern is None or len(entry.pattern) != 5):
            count = "no" if entry.pattern is None else len(entry.pattern)
            return f"{name} is scored with {count} marks: a scored guess has exactly 5"
        if entry.status is not Status.SCORED and entry.pattern is not None:
            return f"{name} is {entry.status.value} but has a pattern: only a scored guess has one"
    return None


def verify_task(arguments, output, reference, workspace):
    entries = []

    def add(identifier, text, ok, expected=None, actual=None, message=""):
        entries.append(constraint(identifier, text, ok, expected, actual, message))
        return ok is True

    def skip(identifier, text, needs):
        entries.append(constraint(identifier, text, None, message=f"Not checked: {needs} did not hold."))

    texts = [
        ("answer-key", "The answer key is this game's, well formed, with the allowed-words list"),
        ("answer-key-rules", "The answer key's feedback follows the rules, recomputed independently"),
        ("submitted-game", "The submission is for this game: one entry per guess, in order, as written"),
        ("patterns-shaped", "A scored guess has 5 marks; an invalid or unplayed guess has none"),
        ("statuses", "Each guess's status (scored, invalid or unplayed) is right"),
        ("patterns", "Each scored guess's marks are right"),
        ("solved", "solved is right"),
        ("attempts", "attempts counts the scored guesses"),
    ]

    # 1 to 4: the gates.
    key = reference
    if key is None:
        problem = "No answer key: load_game never ran for this task."
    elif key.game != arguments.game:
        problem = f"The answer key is for {key.game!r}, not {arguments.game!r}."
    else:
        problem = key_problem(key)
    blocker = None if add(*texts[0], problem is None, message=problem or "") else texts[0][0]
    gates = [
        lambda: key_rules_problem(key),
        lambda: _submitted_game(arguments, output, key),
        lambda: _patterns_shaped(output),
    ]
    for (identifier, text), check in zip(texts[1:GATES], gates):
        if blocker:
            skip(identifier, text, blocker)
            continue
        problem = check()
        if not add(identifier, text, problem is None, message=problem or ""):
            blocker = identifier

    if blocker:
        for identifier, text in texts[GATES:]:
            skip(identifier, text, blocker)
        return result(False, summary(entries), score=0.0, constraints=entries)

    # 5 to 8: the answer, against the verifier's own replay of the game.
    rows, solved, attempts = replay(key.answer, key.guesses, key.allowed)
    wrong_status, wrong_pattern = [], []
    for number, (entry, (status, pattern)) in enumerate(zip(output.feedback, rows), 1):
        if entry.status is not status:
            wrong_status.append((number, entry, status))
        elif status is Status.SCORED and entry.pattern != pattern:
            wrong_pattern.append((number, entry, pattern))

    first = wrong_status[0] if wrong_status else None
    add(
        *texts[4],
        not wrong_status,
        expected=[f"{number}: {status.value}" for number, _, status in wrong_status],
        actual=[f"{number}: {entry.status.value}" for number, entry, _ in wrong_status],
        message=first
        and f"{_numbered(first[0], first[1].guess)} is reported {first[1].status.value}, but the rules make it"
        f" {first[2].value}" + (f"; also wrong: {len(wrong_status) - 1} more" if len(wrong_status) > 1 else ""),
    )
    first = wrong_pattern[0] if wrong_pattern else None
    add(
        *texts[5],
        not wrong_pattern,
        expected=[f"{number}: {shown(pattern)}" for number, _, pattern in wrong_pattern],
        actual=[f"{number}: {shown(entry.pattern)}" for number, entry, _ in wrong_pattern],
        message=first
        and f"{_numbered(first[0], first[1].guess)} is reported {shown(first[1].pattern)}, but the rules give"
        f" {shown(first[2])}" + (f"; also wrong: {len(wrong_pattern) - 1} more" if len(wrong_pattern) > 1 else ""),
    )
    add(*texts[6], output.solved == solved, solved, output.solved,
        f"solved is reported {output.solved}, but the rules give {solved}")
    add(*texts[7], output.attempts == attempts, attempts, output.attempts,
        f"attempts is reported {output.attempts}, but {attempts} guesses are scored")

    if all(entry["ok"] for entry in entries):
        counts = {status: sum(row[0] is status for row in rows) for status in Status}
        outcome = f"solved in {attempts}" if solved else f"not solved after {attempts}"
        message = (
            f"All 8 checks hold: {len(rows)} guesses ({counts[Status.SCORED]} scored, {counts[Status.INVALID]} invalid,"
            f" {counts[Status.UNPLAYED]} unplayed), {outcome} attempts."
        )
        return result(True, message, constraints=entries)
    right = len(rows) - len(wrong_status) - len(wrong_pattern) + (output.solved == solved) + (output.attempts == attempts)
    return result(False, summary(entries), score=min(right / (len(rows) + 2), 0.99), constraints=entries)
