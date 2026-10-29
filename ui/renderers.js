// How this plugin's page draws a refereed game (a ScoreOutput): one row per guess, each letter a tile
// marked HIT (teal), NEAR (coral) or MISS (gray), an invalid or unplayed guess as its word and a pill,
// and the result: solved or not, and the attempts used.
import { h } from "./kit/components.js";

const STATUS_TONE = { invalid: "bad", unplayed: "neutral" };

/** A scored guess's 5 tiles: each letter of the guess with its mark. */
function tiles(guess, pattern) {
  return h(
    "div",
    { class: "tiles" },
    pattern.map((mark, index) => h("span", { class: `tile ${mark.toLowerCase()}`, title: mark, text: (guess[index] ?? "").toUpperCase() })),
  );
}

function row(entry, number) {
  const body =
    entry.status === "scored" && Array.isArray(entry.pattern)
      ? tiles(entry.guess, entry.pattern)
      : h("div", { class: "word" }, h("code", { text: entry.guess }), h("span", { class: `pill tone-${STATUS_TONE[entry.status] ?? "info"}`, text: entry.status }));
  return h("li", { class: "guess" }, h("span", { class: "number", text: String(number) }), body);
}

export default {
  ScoreOutput: (output) =>
    h(
      "div",
      { class: "board" },
      h("p", { class: "outcome", text: `${output.game}: ${output.solved ? "solved" : "not solved"} in ${output.attempts} attempt${output.attempts === 1 ? "" : "s"}` }),
      h("ol", { class: "guesses" }, output.feedback.map((entry, index) => row(entry, index + 1))),
      h(
        "p",
        { class: "legend" },
        h("span", { class: "tile hit", text: "H" }), " HIT ",
        h("span", { class: "tile near", text: "N" }), " NEAR ",
        h("span", { class: "tile miss", text: "M" }), " MISS",
      ),
    ),
};
