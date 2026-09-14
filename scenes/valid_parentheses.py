"""Valid parentheses, checked with a stack, one sentence at a time.

Same contract as bubble_sort, binary_search and kadane: every entry in SCRIPT
pairs a beat name from scripts/valid_parentheses.json with the single visible
action that sentence describes, and `self.beat(name)` writes the sentence as
the caption before the action runs. See scenes/beat_timing.py.

Two inputs, both traced before writing any narration:

  "{[()]}"  (6 chars): push {, push [, push (, then three clean matches
            popping ( -> ), [ -> ], { -> } in that order. Stack ends empty:
            VALID.

  "([)]"    (4 chars): push (, push [, then a closing ) arrives while the
            stack top is [, not (. MISMATCH at index 2 -- the algorithm
            halts there; index 3 (']') is never examined.

Neither case degenerates the way binary search's first attempt did: the
valid string exercises three real pushes and three real pops, and the
invalid string fails on a genuine top-of-stack clash rather than on the
first character.

CAUTION specific to this topic: captions render through
MathTex(r"\\text{...}"), and "{" / "}" are LaTeX-reserved -- an unescaped
brace in narration breaks the caption. Every sentence refers to brackets by
name ("opening curly brace"), never by literal symbol. On-screen glyphs use
Text() (Pango), not MathTex, so the literal characters are safe there.

Run tools/build_topic.py first; without measured timings the beats fall back
to FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

CASE1 = "{[()]}"
CASE2 = "([)]"

CELL_SIZE = 0.85
CELL_GAP = 1.1
ARRAY_Y = -1.3            # string row
STRING_CENTER_X = -1.8    # shifted left to leave the stack lane clear
STACK_X = 5.0             # fixed lane; stays put across both cases
STACK_BASE_Y = -1.3       # same height as the string: "beside it"
CHIP_GAP = 0.85
VERDICT_Y = 2.3
MAX_CAPTION_W = 11.5

CHIP_STROKE = BLUE_D
CHIP_FILL = BLUE_E
MATCH_COLOR = GREEN
FAIL_COLOR = RED

# (beat name, action method, args). One row per narration sentence, hardcoded
# from the trace above -- the SCRIPT table *is* the trace.
SCRIPT = [
    ("intro_string1", "reveal_string", (CASE1,)),
    ("intro_stack", "show_stack_area", ()),
    ("intro_push_rule", "add_rule", ("opening bracket: push",)),
    ("intro_pop_rule", "add_rule", ("closing bracket: pop and check top",)),
    ("intro_fail_rule", "add_rule", ("no match: invalid", FAIL_COLOR)),

    ("c1_push0", "push", (0,)),
    ("c1_push1", "push", (1,)),
    ("c1_push2", "push", (2,)),
    ("c1_pop0", "match", (3,)),
    ("c1_pop1", "match", (4,)),
    ("c1_pop2", "match", (5,)),
    ("c1_verdict", "show_valid", ()),

    ("why_lifo", "clear_case1", ()),

    ("c2_intro", "reveal_string", (CASE2,)),
    ("c2_push0", "push", (0,)),
    ("c2_push1", "push", (1,)),
    ("c2_mismatch", "mismatch", (2,)),
    ("c2_fail", "show_invalid", (3,)),

    ("an_contrast", "emphasize_fail_rule", ()),
    ("an_seen_both", "clear_case2", ()),
    ("an_onepass", "show_on", ()),
    ("an_space", "show_space", ()),
    ("an_naive", "show_naive", ()),
    ("an_realworld", "pulse_title", ()),
    ("an_summary", "clear_formula", ()),

    ("end_line", "fade_out", ()),
]

ACTION_P = 0.40


class ValidParentheses(TimedScene):
    TOPIC = "valid_parentheses"
    STATUS_AT = DOWN * 3.2

    def construct(self):
        self.setup_timing()
        self.cells: list[VGroup] = []
        self.stack_items: list[VGroup] = []
        self.current_string = ""
        self.string_group = None
        self.stack_label = None
        self.stack_base = None
        self.rules: list[Mobject] = []
        self.rule_group = VGroup()
        self.verdict = None
        self.formula = None

        self.build_stage()
        for name, action, args in SCRIPT:
            with self.beat(name) as clock:
                getattr(self, action)(clock, *args)

    # ------------------------------------------------------------------ setup

    def make_caption(self, text: str) -> Mobject:
        mobject = MathTex(r"\text{" + text + "}", color=GREY_A).scale(0.72)
        if mobject.width > MAX_CAPTION_W:
            mobject.scale_to_fit_width(MAX_CAPTION_W)
        return mobject

    def build_stage(self):
        self.title = Text("Valid Parentheses", weight=BOLD).scale(0.8).to_edge(UP, buff=0.4)
        self.add(self.title)

    def slot_x(self, i: int, n: int) -> float:
        return STRING_CENTER_X + (i - (n - 1) / 2) * CELL_GAP

    def make_chip(self, ch: str, size: float) -> VGroup:
        """A square-with-glyph, used for both string slots and stack chips.

        Text(), not MathTex: bracket glyphs are literal characters here, and
        curly braces would break LaTeX parsing if this went through MathTex.
        """
        square = Square(side_length=size, stroke_width=4, color=CHIP_STROKE)
        square.set_fill(CHIP_FILL, opacity=0.3)
        label = Text(ch, weight=BOLD).scale(size)
        return VGroup(square, label)

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_string(self, c: BeatClock, s: str):
        """Lay out a fresh string and reset the per-case state (stack, cells)."""
        self.current_string = s
        n = len(s)
        self.cells = [
            self.make_chip(ch, CELL_SIZE).move_to([self.slot_x(i, n), ARRAY_Y, 0])
            for i, ch in enumerate(s)
        ]
        self.string_group = VGroup(*self.cells)
        self.stack_items = []
        c.play(
            LaggedStart(*(GrowFromCenter(cell) for cell in self.cells), lag_ratio=0.3),
            p=ACTION_P,
            cap=2.4,
        )

    def show_stack_area(self, c: BeatClock):
        self.stack_label = Text("stack", weight=BOLD).scale(0.5).set_color(GREY_B)
        self.stack_label.move_to([STACK_X, STACK_BASE_Y - 0.9, 0])
        self.stack_base = Line(
            [STACK_X - 0.5, STACK_BASE_Y - 0.55, 0], [STACK_X + 0.5, STACK_BASE_Y - 0.55, 0],
            color=GREY_C, stroke_width=3,
        )
        c.play(FadeIn(self.stack_label), FadeIn(self.stack_base), p=ACTION_P, cap=1.6)

    def add_rule(self, c: BeatClock, text: str, colour=GREY_A):
        """Grow a small persistent legend in the corner, one line per beat."""
        line = MathTex(r"\text{" + text + "}", color=colour).scale(0.5)
        if not self.rules:
            line.to_corner(UL, buff=0.5)
        else:
            line.next_to(self.rules[-1], DOWN, buff=0.15, aligned_edge=LEFT)
        self.rules.append(line)
        self.rule_group.add(line)
        c.play(Write(line), p=ACTION_P, cap=1.8)

    def push(self, c: BeatClock, i: int):
        """The character flies from its string slot to the top of the stack."""
        ch = self.current_string[i]
        depth = len(self.stack_items)
        chip = self.make_chip(ch, CELL_SIZE * 0.85).move_to(self.cells[i].get_center())
        self.add(chip)  # starts exactly where the string glyph already sits
        self.stack_items.append(chip)
        target = self.make_chip(ch, CELL_SIZE * 0.85).move_to(
            [STACK_X, STACK_BASE_Y + depth * CHIP_GAP, 0]
        )
        c.play(
            Transform(chip, target),
            self.cells[i][1].animate.set_opacity(0),  # the origin slot empties out
            p=ACTION_P,
            cap=1.8,
        )

    def match(self, c: BeatClock, i: int):
        """A closing bracket meets the top of the stack: both vanish together."""
        top = self.stack_items.pop()
        cell = self.cells[i]
        c.play(
            Flash(top.get_center(), color=MATCH_COLOR, flash_radius=0.5),
            FadeOut(top, scale=0.4),
            FadeOut(cell[1], scale=0.4),
            cell[0].animate.set_stroke(opacity=0.2).set_fill(opacity=0.05),
            p=ACTION_P,
            cap=1.8,
        )

    def mismatch(self, c: BeatClock, i: int):
        """A closing bracket meets a top that does not match: both flag red, stay put."""
        top = self.stack_items[-1]  # left in place, unpopped -- this is where it broke
        cell = self.cells[i]
        c.play(
            Flash(top.get_center(), color=FAIL_COLOR, flash_radius=0.4),
            Flash(cell.get_center(), color=FAIL_COLOR, flash_radius=0.4),
            top[0].animate.set_stroke(FAIL_COLOR, width=6).set_fill(FAIL_COLOR, opacity=0.35),
            cell[0].animate.set_stroke(FAIL_COLOR, width=6).set_fill(FAIL_COLOR, opacity=0.25),
            Wiggle(top),
            Wiggle(cell),
            p=ACTION_P,
            cap=2.2,
        )

    def show_valid(self, c: BeatClock):
        self.verdict = Text("VALID", weight=BOLD, color=MATCH_COLOR).scale(1.1)
        self.verdict.move_to([0, VERDICT_Y, 0])
        c.play(Write(self.verdict), p=ACTION_P, cap=2.0)

    def show_invalid(self, c: BeatClock, from_index: int):
        """Stamp the verdict and grey out whatever was never even examined."""
        self.verdict = Text("INVALID", weight=BOLD, color=FAIL_COLOR).scale(1.1)
        self.verdict.move_to([0, VERDICT_Y, 0])
        anims = [Write(self.verdict)]
        anims += [cell.animate.set_opacity(0.15) for cell in self.cells[from_index:]]
        c.play(*anims, p=ACTION_P, cap=2.0)

    def clear_case1(self, c: BeatClock):
        c.play(FadeOut(self.string_group), FadeOut(self.verdict), p=ACTION_P, cap=1.8)

    def clear_case2(self, c: BeatClock):
        leftover = VGroup(*self.stack_items)  # the mismatched pair, never popped
        c.play(
            FadeOut(self.string_group), FadeOut(self.verdict), FadeOut(leftover),
            p=ACTION_P, cap=2.0,
        )
        self.stack_items = []

    def emphasize_fail_rule(self, c: BeatClock):
        c.play(Circumscribe(self.rules[-1], color=FAIL_COLOR, buff=0.15), p=ACTION_P, cap=1.8)

    def show_on(self, c: BeatClock):
        self.formula = MathTex(r"O(n)", color=CHIP_STROKE).scale(1.2).move_to([0, VERDICT_Y, 0])
        c.play(Write(self.formula), p=ACTION_P, cap=1.8)

    def show_space(self, c: BeatClock):
        new = MathTex(
            r"O(n) \text{ time}, \; O(n) \text{ space}"
        ).scale(0.85).move_to([0, VERDICT_Y, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def show_naive(self, c: BeatClock):
        new = MathTex(r"O(n) \;\text{vs}\; O(n^2)").scale(0.85).move_to([0, VERDICT_Y, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def pulse_title(self, c: BeatClock):
        c.play(Indicate(self.title, scale_factor=1.08, color=CHIP_STROKE), p=ACTION_P, cap=1.8)

    def clear_formula(self, c: BeatClock):
        c.play(FadeOut(self.formula), p=ACTION_P, cap=1.4)

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(self.title, self.rule_group, self.stack_label, self.stack_base)),
            p=ACTION_P,
            cap=2.2,
        )
