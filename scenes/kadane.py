"""Kadane's algorithm (maximum subarray) on [-2, 1, -3, 4, -1, 2, 1, -5, 4],
one sentence at a time.

Same contract as bubble_sort and binary_search: every entry in SCRIPT pairs a
beat name from scripts/kadane.json with the single visible action that
sentence describes, and `self.beat(name)` writes the sentence as the caption
before the action runs. See scenes/beat_timing.py.

Variant: reset-to-zero Kadane. running_sum starts at 0; at each index we add
a[i], record a new best whenever running_sum exceeds it, and reset
running_sum to 0 whenever it goes negative (a negative running sum can never
help a future subarray, so nothing is lost by dropping it). best is
initialized to 0 rather than -infinity, which only costs correctness on an
all-negative array -- not the case here -- and pays for itself pedagogically:
"best so far" starts at a real, meaningful value ("we have found no positive
run yet") and, exactly as the visual brief asks, only ever moves up.

Traced on the exact input before writing any narration (see build history):
  i  a[i]  running  best  event
  0    -2        0     0  RESET
  1     1        1     1  RECORD
  2    -3        0     1  RESET
  3     4        4     4  RECORD
  4    -1        3     4
  5     2        5     5  RECORD
  6     1        6     6  RECORD
  7    -5        1     6
  8     4        5     6
Final: best = 6, from the subarray a[3:7] = [4, -1, 2, 1]. Two resets, four
records, three no-ops -- enough variety to exercise all three requested
visuals (dropping bar, rising marker, winning bracket) without a degenerate
one-probe case like binary_search's inclusive-bounds trap.

Run tools/build_topic.py first; without measured timings the beats fall back
to FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

VALUES = [-2, 1, -3, 4, -1, 2, 1, -5, 4]

CELL_SIZE = 0.85
CELL_GAP = 1.25
ARRAY_Y = -1.4
BASELINE_Y = 0.3      # the running-sum bar's zero line
SCALE = 0.35           # vertical units per unit of running sum
MAX_CAPTION_W = 11.5

POS_COLOR = GREEN
NEG_COLOR = RED
BEST_COLOR = GOLD
BASE_COLOR = GREY_C

# (beat name, action method, args). One row per narration sentence, hardcoded
# from the trace above -- the SCRIPT table *is* the trace.
SCRIPT = [
    ("intro_array", "reveal_array", ()),
    ("intro_goal", "show_goal", ()),
    ("intro_running", "show_running_bar", ()),
    ("intro_reset", "show_reset_rule", ()),
    ("intro_best", "show_best_marker", ()),

    ("p0_extend", "extend", (0,)),
    ("p0_reset", "reset_bar", (0,)),

    ("p1_extend", "extend", (1,)),
    ("p1_record", "record", (1,)),

    ("p2_extend", "extend", (2,)),
    ("p2_reset", "reset_bar", (2,)),

    ("p3_extend", "extend", (3,)),
    ("p3_record", "record", (3,)),

    ("p4_extend", "extend", (4,)),

    ("p5_extend", "extend", (5,)),
    ("p5_record", "record", (5,)),

    ("p6_extend", "extend", (6,)),
    ("p6_record", "record", (6,)),

    ("p7_extend", "extend", (7,)),

    ("p8_extend", "extend", (8,)),

    ("an_final", "emphasize_best", ()),
    ("an_bracket", "bracket_subarray", ()),
    ("an_sumcheck", "show_sum_equation", ()),
    ("an_pass", "sweep_pass", ()),
    ("an_linear", "show_on", ()),
    ("an_contrast", "show_on2", ()),

    ("end_line", "fade_out", ()),
]

ACTION_P = 0.40


class Kadane(TimedScene):
    TOPIC = "kadane"
    STATUS_AT = DOWN * 3.2

    def construct(self):
        self.setup_timing()
        self.running = 0
        self.best = 0
        self.current_start = 0
        self.best_start = 0
        self.best_end = 0
        self.bar = None
        self.best_marker = None
        self.baseline = None
        self.reset_rule = None
        self.goal_badge = None
        self.bracket = None
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

    def slot_x(self, i: int) -> float:
        return (i - (len(VALUES) - 1) / 2) * CELL_GAP

    def build_stage(self):
        self.title = Text("Kadane's Algorithm", weight=BOLD).scale(0.8).to_edge(UP, buff=0.4)
        self.add(self.title)

        self.cells = []
        for i, value in enumerate(VALUES):
            square = Square(side_length=CELL_SIZE, stroke_width=4, color=BLUE_D)
            square.set_fill(BLUE_E, opacity=0.3)
            label = MathTex(str(value)).scale(0.8)
            cell = VGroup(square, label).move_to([self.slot_x(i), ARRAY_Y, 0])
            self.cells.append(cell)
        self.array = VGroup(*self.cells)

    # --------------------------------------------------------------- helpers

    def running_bar(self, i: int, value: int) -> Rectangle:
        """A bar over slot i whose height and sign show the running sum."""
        height = max(abs(value) * SCALE, 0.04)
        colour = POS_COLOR if value >= 0 else NEG_COLOR
        bar = Rectangle(
            width=0.55, height=height, stroke_width=2,
            color=colour, fill_color=colour, fill_opacity=0.55,
        )
        y = BASELINE_Y + (height / 2 if value >= 0 else -height / 2)
        bar.move_to([self.slot_x(i), y, 0])
        return bar

    def best_marker_group(self, value: int) -> VGroup:
        """A dashed high-water line plus label. Only ever asked to move up."""
        y = BASELINE_Y + value * SCALE
        line = DashedLine(
            [self.slot_x(0) - 0.6, y, 0], [self.slot_x(len(VALUES) - 1) + 0.6, y, 0],
            color=BEST_COLOR, stroke_width=3,
        )
        label = Text(f"best: {value}", weight=BOLD).scale(0.4).set_color(BEST_COLOR)
        label.next_to(line, RIGHT, buff=0.15)
        return VGroup(line, label)

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_array(self, c: BeatClock):
        c.play(
            LaggedStart(*(GrowFromCenter(cell) for cell in self.cells), lag_ratio=0.3),
            p=ACTION_P,
            cap=2.4,
        )

    def show_goal(self, c: BeatClock):
        self.goal_badge = MathTex(
            r"\text{goal: largest contiguous sum}", color=BEST_COLOR
        ).scale(0.5).to_corner(UL, buff=0.5)
        c.play(FadeIn(self.goal_badge, shift=RIGHT * 0.2), p=ACTION_P, cap=1.4)

    def show_running_bar(self, c: BeatClock):
        self.baseline = DashedLine(
            [self.slot_x(0) - 0.7, BASELINE_Y, 0],
            [self.slot_x(len(VALUES) - 1) + 0.7, BASELINE_Y, 0],
            color=BASE_COLOR, stroke_width=2,
        )
        self.bar = self.running_bar(0, 0)
        c.play(FadeIn(self.baseline), FadeIn(self.bar), p=ACTION_P, cap=1.8)

    def show_reset_rule(self, c: BeatClock):
        self.reset_rule = MathTex(
            r"\text{sum} < 0 \;\Rightarrow\; \text{reset to } 0", color=NEG_COLOR
        ).scale(0.55).to_corner(UR, buff=0.5)
        c.play(Write(self.reset_rule), p=ACTION_P, cap=1.8)

    def show_best_marker(self, c: BeatClock):
        self.best_marker = self.best_marker_group(0)
        c.play(FadeIn(self.best_marker, shift=UP * 0.15), p=ACTION_P, cap=1.6)

    def extend(self, c: BeatClock, i: int):
        """Add a[i] into the running sum; the bar moves to slot i and rescales."""
        self.running += VALUES[i]
        new_bar = self.running_bar(i, self.running)
        c.play(Transform(self.bar, new_bar), p=ACTION_P, cap=1.6)

    def reset_bar(self, c: BeatClock, i: int):
        """Running sum went negative: drop it back to zero at the same slot."""
        self.running = 0
        self.current_start = i + 1
        new_bar = self.running_bar(i, 0)
        c.play(Transform(self.bar, new_bar), p=ACTION_P, cap=1.6)

    def record(self, c: BeatClock, i: int):
        """New best: the marker rises to the running sum's current value."""
        self.best = self.running
        self.best_start = self.current_start
        self.best_end = i
        new_marker = self.best_marker_group(self.best)
        c.play(Transform(self.best_marker, new_marker), p=ACTION_P, cap=1.6)

    def emphasize_best(self, c: BeatClock):
        """Scan is over; the reset rule has done its job and can go."""
        c.play(
            Indicate(self.best_marker, scale_factor=1.12, color=BEST_COLOR),
            FadeOut(self.reset_rule),
            p=ACTION_P,
            cap=2.0,
        )

    def bracket_subarray(self, c: BeatClock):
        group = VGroup(*self.cells[self.best_start:self.best_end + 1])
        brace = Brace(group, DOWN, buff=0.35, color=BEST_COLOR)
        label = brace.get_text(f"sum = {self.best}").set_color(BEST_COLOR).scale(0.6)
        self.bracket = VGroup(brace, label)
        c.play(FadeIn(self.bracket, shift=UP * 0.2), p=ACTION_P, cap=1.8)

    def show_sum_equation(self, c: BeatClock):
        self.formula = MathTex(r"4 + (-1) + 2 + 1 = 6").scale(0.8).move_to([0, 2.7, 0])
        c.play(Write(self.formula), p=ACTION_P, cap=1.8)

    def sweep_pass(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.08, color=POS_COLOR) for cell in self.cells),
                lag_ratio=0.12,
            ),
            p=ACTION_P + 0.10,
            cap=2.6,
        )

    def show_on(self, c: BeatClock):
        new = MathTex(r"O(n)", color=BEST_COLOR).scale(1.2).move_to([0, 2.7, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def show_on2(self, c: BeatClock):
        new = MathTex(r"O(n) \;\text{vs}\; O(n^2)").scale(0.85).move_to([0, 2.7, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(
                VGroup(
                    self.array, self.bar, self.best_marker, self.baseline,
                    self.bracket, self.formula, self.title, self.goal_badge,
                )
            ),
            p=ACTION_P,
            cap=2.2,
        )
