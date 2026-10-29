# Guess Referee

A `nanoagent.plugin/v0001` plugin. Its task, `score-game`, has an agent referee
one game of a five-letter word-guessing game: given a bundled game file (a
hidden word and a list of guesses, at most 6 of which may be scored) and a
bundled allowed-words list, it reports each guess's status and its 5 marks,
whether the game was solved, and in how many attempts. No network. The
verifier replays the game under the rules below, in its own code, and judges
every entry.

## Tools

| Tool | Does | Code |
|---|---|---|
| `load_game` | The answer key: the game, the whole allowed-words list, and each guess's feedback under the rules. The agent never sees it | `src/plugin/game.py`, `src/plugin/rules.py` |
| `read_game` | A game's hidden word, max attempts (always 6) and guesses, exactly as written | `src/plugin/game.py` |
| `check_words` | For each word, whether it is 5 ASCII letters and, lowercased, in the allowed-words list: rule 2 exactly | `src/plugin/game.py` |
| `letters_in_word` | A distractor: the hidden word's distinct letters, sorted. True, but it drops repeated letters, so it cannot tell how many copies may be marked NEAR | `src/plugin/game.py` |
| `check_shape` | A distractor: whether each word is 5 ASCII letters. True, but it never reads the allowed-words list, so it is not rule 2 | `src/plugin/game.py` |

No tool scores a guess: the agent applies the scoring rule itself. Its plan is
`read_game`, `check_words` with every guess, then `submit`: three tool calls.

### Tasks

| Task | Does | Runner |
|---|---|---|
| `score-game` | Referees one bundled game: each guess's status and pattern, whether it was solved, and the attempts used | `agent`, with `read_game`, `check_words`, `letters_in_word` and `check_shape`; reference `load_game` |

## The rules

1. **Scoring is two-pass, with three marks.** HIT: the right letter in the
   right position. NEAR: a letter in the hidden word but not at this position,
   with an unused copy of it remaining. MISS: otherwise. First every position
   whose letter equals the hidden word's letter there is HIT, and uses up that
   letter of the hidden word. Then, left to right over the other positions, a
   letter is NEAR only if the hidden word still has an unused copy of it;
   otherwise MISS. Guessing LLAMA against a word with one L marks at most one
   L as HIT or NEAR, and ALARM against PLANT is MISS HIT HIT MISS MISS: the
   HIT A uses up the only A before the first A is looked at.
2. **Invalid.** A guess that is not exactly 5 ASCII letters (A to Z, either
   case), or whose lowercase form is not in the allowed-words list, is INVALID:
   no pattern, and it does not use up an attempt. Guesses are not trimmed:
   `" crane"` is invalid. A letter outside ASCII is invalid even when
   lowercasing would make it ASCII (U+212A, the Kelvin sign, lowercases to
   `k`, so `\u212anife` is invalid though `knife` is allowed).
3. **Unplayed.** Once a scored guess equals the hidden word, or 6 guesses are
   scored, the game is over: every later guess is UNPLAYED, with no pattern,
   even one that would be invalid. UNPLAYED takes precedence over INVALID.
4. **Case.** Guesses are case-insensitive: a guess is lowercased before it is
   looked up or scored. Each entry still copies the guess exactly as written.
5. **The rest.** Every other guess is SCORED and uses one attempt; a repeated
   guess is scored again. `solved` is true when a scored guess equals the
   hidden word; `attempts` is the number of scored guesses, solved or not.
6. **A game file** is `{"answer", "max_attempts", "guesses"}`: the answer 5
   lowercase letters in the allowed-words list, `max_attempts` 6, and 1 to 12
   guesses. Any other file is refused with an error, never repaired.

## Games

The bundled games, in `src/plugin/data/games/`, each built around traps.
H is HIT, N NEAR, `.` MISS; the expectations were derived by hand
(`tests/expected.py`) and both implementations are tested against them.

| Game | Guesses and their feedback | Result | Traps |
|---|---|---|---|
| `hotel.json` | llama `N....`, hello `HNN.N`, hotel `HHHHH`, crane unplayed | solved, 3 | a repeated letter in the guess only; a guess after the solve |
| `creep.json` | eight `N....`, geese `.NH..`, crepe `HHHNN`, sweep `..HHH`, creed `HHHH.`, cheep `H.HHH`, creep unplayed | not solved, 6 | a repeated letter in the answer only; six wrong guesses; the answer as a 7th guess |
| `plant.json` | alarm `.HH..`, xqzvy invalid, plan invalid, slant `.HHHH`, giant `..HHH`, blank `.HHH.`, plane `HHHH.`, PLANT `HHHHH`, plant unplayed | solved, 6 | a HIT copy before a would-be NEAR one; invalid guesses that use no attempt; solved on the 6th attempt |
| `crane.json` | Llama `..H..`, TRACE `.HHNH`, cRaNe `HHHHH`, zzzzz unplayed, crane unplayed | solved, 3 | mixed case; an invalid word after the solve is unplayed |

## Constraints

`verifier/task.py` judges the submission against 8 constraints, in order.
Every entry of the verdict's `details.constraints` has the keys
`{id, constraint, ok, expected, actual, message}`; `ok` is `true`, `false`, or
`null` when a check it needs did not hold.

| # | id | What it checks | Example failure message |
|---|---|---|---|
| 1 | `answer-key` | The answer key is this game's and well formed, with an allowed-words list holding its answer | No answer key: load_game never ran for this task. |
| 2 | `answer-key-rules` | The key's feedback equals the verifier's own replay of the game | the answer key's guess 1 'llama' breaks the rules |
| 3 | `submitted-game` | The submission is for this game: one entry per guess, in order, copied as written | entry 2 is 'trace', but the game's guess 2 is 'TRACE': copy each guess exactly as written |
| 4 | `patterns-shaped` | A scored guess has 5 marks; an invalid or unplayed one has none | guess 4 'zzzzz' is unplayed but has a pattern: only a scored guess has one |
| 5 | `statuses` | Each guess's status is right | guess 4 'zzzzz' is reported invalid, but the rules make it unplayed |
| 6 | `patterns` | Each scored guess's marks are right | guess 1 'alarm' is reported NEAR HIT HIT MISS MISS, but the rules give MISS HIT HIT MISS MISS |
| 7 | `solved` | `solved` is right | solved is reported False, but the rules give True |
| 8 | `attempts` | `attempts` counts the scored guesses | attempts is reported 4, but 3 guesses are scored |

How it is scored:

- **Valid** only when all 8 hold; the score is then 1.0.
- **Score 0** when any of 1 to 4 fails: they guard the answer key and the submission's integrity.
- **Otherwise** the score is (guesses whose status and pattern are both right, plus 1 if `solved` is right, plus 1 if `attempts` is right) divided by (guesses + 2), at most 0.99.
- **The message** names the first failing constraint, why, and how many more fail.

`verifier/rules.py` is a second implementation of the rules that shares no code
with `src/plugin/rules.py`: it decides a NEAR by counting (a non-HIT
position is NEAR when it is among the first k non-HIT positions holding its
letter, k being how many non-HIT positions of the answer hold it) instead of
using up copies one by one. Constraint 2 checks that the answer key agrees with
it, so a wrong rule would have to be written the same wrong way twice to pass.
Every tool call is checked as well: `verify_input` refuses a malformed game
name or an empty word list, and `verify_output` holds each tool's output to
what it promises.

## Limitations

- **Only the bundled games.** The task input names one of the games in
  `src/plugin/data/games/`; a person cannot bring a game file of their own.
- **No provenance gate.** The plugin writes no files, so the verifier cannot
  prove the agent called `read_game`. The answer depends entirely on the hidden
  word and the list, which only the tools give, so a correct answer without
  them would be a guess.
- **The list is small.** The allowed-words list is about 600 common words;
  a real word outside it is INVALID by rule 2.
- **The hidden word is shown.** The agent is the referee, not a player, so
  `read_game` gives it the answer.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions (none), tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable names this plugin needs (none)
├── src/plugin/      # the MCP server (__main__.py), the tools (game.py), the rules (rules.py)
│   └── data/        # words.txt, the allowed-words list, and games/, the bundled game files
├── tests/           # hand-derived answers (expected.py), both rule implementations, the tools, the verifier
├── ui/              # how the page draws a ScoreOutput: a board of tiles, HIT teal, NEAR coral, MISS gray
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier: one module per tool, rules.py, and the task's 8 constraints in task.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv lock --check
```

With the `nanoagent` CLI installed in a separate environment:

```bash
nanoagent plugin inspect .                        # every plugin rule
nanoagent plugin agent config=run.yaml home=out   # the agent task; needs OPENROUTER_API_KEY
```

A `run.yaml` for one game (`args.json` holds the task input, e.g.
`{"game": "plant.json"}`; give `plugin` and `arguments` as absolute paths).
The run folder gets `result.json`, `reference.json`, `messages.json` and
`verdict.json`, and the command exits 1 unless the verdict is valid:

```yaml
_ > nanoagent.cli.plugin.PluginOpenRouterAgentConfig:
plugin: /path/to/word-guess
task: score-game
arguments: /path/to/args.json
inputs: []
timeout: 60
llm > nanoagent.llm.openrouter.OpenRouterConfig:
  model: deepseek/deepseek-v4-flash-0731
  max_tokens: null
  temperature: null
  max_attempts: 3
  read_timeout: 180
  input_price: 0.0
  output_price: 0.0
harness > nanoagent.harness.nanoagent.NanoAgentConfig:
  max_steps: 8
  cost_limit: null
  token_limit: null
  context_window: null
  hooks: []
  skills: null
  context_files: []
  events: null
```
