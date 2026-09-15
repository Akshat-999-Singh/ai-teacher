"""The Euclidean algorithm as repeated square-carving, one sentence at a time.

Same contract as bubble_sort, binary_search, kadane and valid_parentheses:
every entry in SCRIPT pairs a beat name from scripts/euclidean_gcd.json with
the single visible action that sentence describes, and `self.beat(name)`
writes the sentence as the caption before the action runs. See
scenes/beat_timing.py.

Traced before writing any narration (gcd(48, 18)):
  48 = 2 x 18 + 12   (carve two 18x18 squares)
  18 = 1 x 12 + 6    (carve one 12x12 square)
  12 = 2 x 6 + 0     (carve two 6x6 squares -- remainder 0, done)
  gcd = 6.  5 squares total, area 2*18^2 + 12^2 + 2*6^2 = 864 = 48*18 exactly:
  the decomposition tiles the whole rectangle with no gaps or overlap.
  Because 6 divides both 48 and 18, the same rectangle can *also* be tiled by
  a uniform 8x3 grid of 6x6 squares -- a second, independent geometric fact
  that is the actual reason 6 is "the" answer rather than just "an" answer.
  Neither trace degenerates the way binary search's first attempt did: three
  real division steps, with 2, 1 and 2 squares respectively.

Geometry: the remaining rectangle is tracked as (rx, ry, rw, rh) in scene
units. `carve()` always cuts along whichever side is currently LONGER, using
a square sized to the SHORTER side -- that alone reproduces the algorithm's
alternating orientation (cut along width, then height, then width again)
with no per-call special-casing; only the square's *size* is hardcoded per
call, taken straight from the trace above.

Run tools/build_topic.py first; without measured timings the beats fall back
to FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

SCALE = 0.13
RECT_W = 48 * SCALE
RECT_H = 18 * SCALE
RECT_X0 = -6.3
RECT_Y0 = 0.4

TRACE_X = 3.0
TRACE_Y0 = 2.6
TRACE_GAP = 0.55

HEADLINE_Y = -1.5
# Clears the caption below (>=0.71 units, worst case) and the gcd stamp above
# (>=0.10 units) for every formula shown here, the tallest being the fraction.
FORMULA_Y = -2.2
MAX_CAPTION_W = 11.5

STEP1_COLOR = TEAL
STEP2_COLOR = ORANGE
GCD_COLOR = GOLD
NEUTRAL_COLOR = BLUE_D

# (beat name, action method, args). One row per narration sentence, hardcoded
# from the trace above -- the SCRIPT table *is* the trace.
SCRIPT = [
    ("intro_rect", "reveal_rect", ()),
    ("intro_goal", "show_goal", ()),
    ("intro_history", "pulse_title", ()),
    ("intro_rule", "add_rule", ("cut the largest square that fits",)),
    ("intro_stop", "add_rule", ("stop when nothing is left over",)),
    ("intro_track", "show_trace_heading", ()),

    ("s1_square1", "carve", (18, STEP1_COLOR)),
    ("s1_square2", "carve", (18, STEP1_COLOR)),
    ("s1_remainder", "write_remainder", (48, 2, 18, 12)),

    ("s2_square1", "carve", (12, STEP2_COLOR)),
    ("s2_remainder", "write_remainder", (18, 1, 12, 6)),

    ("s3_square1", "carve", (6, GCD_COLOR)),
    ("s3_square2", "carve", (6, GCD_COLOR)),
    ("s3_remainder", "write_remainder", (12, 2, 6, 0)),

    ("gcd_reveal", "show_gcd", ()),
    ("gcd_why", "emphasize_squares", ()),

    ("retile_intro", "clear_decomposition", ()),
    ("retile_grid", "show_grid", ()),
    ("retile_proof", "emphasize_grid", ()),
    ("retile_toobig", "show_toobig", ()),

    ("an_recap", "emphasize_trace", ()),
    ("an_onlogsteps", "show_complexity", ()),
    ("an_contrast", "show_contrast", ()),
    ("an_fraction", "show_fraction", ()),
    ("an_summary", "clear_formula", ()),

    ("end_line", "fade_out", ()),
]

ACTION_P = 0.40


class EuclideanGcd(TimedScene):
    TOPIC = "euclidean_gcd"
    STATUS_AT = DOWN * 3.4

    def construct(self):
        self.setup_timing()
        self.rx = self.ry = self.rw = self.rh = 0.0
        self.carved_squares: list[VGroup] = []
        self.trace_lines: list[Mobject] = []
        self.rules: list[Mobject] = []
        self.rule_group = VGroup()
        self.goal_badge = None
        self.trace_heading = None
        self.gcd_stamp = None
        self.grid = None
        self.toobig_group = None
        self.formula = None
        self.dim_labels = None
        self.boundary = None

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
        self.title = Text("Euclidean Algorithm", weight=BOLD).scale(0.75).to_edge(UP, buff=0.4)
        self.add(self.title)

    def make_square(self, size: float, colour) -> VGroup:
        sq = Square(side_length=size, stroke_width=4, color=colour)
        sq.set_fill(colour, opacity=0.35)
        return sq

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_rect(self, c: BeatClock):
        self.boundary = Rectangle(width=RECT_W, height=RECT_H, stroke_width=5, color=WHITE)
        self.boundary.move_to([RECT_X0 + RECT_W / 2, RECT_Y0 + RECT_H / 2, 0])
        self.rx, self.ry, self.rw, self.rh = RECT_X0, RECT_Y0, RECT_W, RECT_H

        label_w = Text("48", weight=BOLD).scale(0.5).move_to([RECT_X0 + RECT_W / 2, RECT_Y0 - 0.35, 0])
        label_h = Text("18", weight=BOLD).scale(0.5).move_to([RECT_X0 - 0.35, RECT_Y0 + RECT_H / 2, 0])
        self.dim_labels = VGroup(label_w, label_h)

        c.play(Create(self.boundary), Write(self.dim_labels), p=ACTION_P, cap=2.4)

    def show_goal(self, c: BeatClock):
        self.goal_badge = MathTex(
            r"\text{goal: gcd}(48, 18)", color=GCD_COLOR
        ).scale(0.5).to_corner(UL, buff=0.5)
        c.play(FadeIn(self.goal_badge, shift=RIGHT * 0.2), p=ACTION_P, cap=1.4)

    def pulse_title(self, c: BeatClock):
        c.play(Indicate(self.title, scale_factor=1.08, color=GCD_COLOR), p=ACTION_P, cap=1.8)

    def add_rule(self, c: BeatClock, text: str):
        """Grow a small persistent legend in the corner, one line per beat."""
        line = MathTex(r"\text{" + text + "}", color=GREY_A).scale(0.5)
        if not self.rules:
            line.to_corner(UR, buff=0.5)
        else:
            line.next_to(self.rules[-1], DOWN, buff=0.15, aligned_edge=RIGHT)
        self.rules.append(line)
        self.rule_group.add(line)
        c.play(Write(line), p=ACTION_P, cap=1.8)

    def show_trace_heading(self, c: BeatClock):
        self.trace_heading = Text("arithmetic", weight=BOLD).scale(0.5).set_color(GREY_B)
        self.trace_heading.move_to([TRACE_X, TRACE_Y0, 0])
        c.play(Write(self.trace_heading), p=ACTION_P, cap=1.6)

    def carve(self, c: BeatClock, size_actual: int, colour):
        """Cut one size_actual^2 square from whichever side is currently longer.

        The square's side always equals the currently SHORTER side of the
        remaining rectangle -- that constraint alone (not any per-call
        special-casing) is what makes the cut direction alternate correctly.
        """
        size = size_actual * SCALE
        if self.rw > self.rh + 1e-6:
            pos = [self.rx + size / 2, self.ry + self.rh / 2, 0]
            self.rx += size
            self.rw -= size
        else:
            pos = [self.rx + self.rw / 2, self.ry + size / 2, 0]
            self.ry += size
            self.rh -= size

        sq = self.make_square(size, colour).move_to(pos)
        # Prior squares dim in the same motion that grows the new one, so the
        # decomposition accumulates with the most recent cut standing out.
        dim_anims = [
            prev.animate.set_stroke(opacity=0.35).set_fill(opacity=0.12)
            for prev in self.carved_squares
        ]
        self.carved_squares.append(sq)
        c.play(GrowFromCenter(sq), *dim_anims, p=ACTION_P, cap=1.8)

    def write_remainder(self, c: BeatClock, a: int, q: int, b: int, r: int):
        """Add one line to the arithmetic trace; tie it to the leftover geometry."""
        n = len(self.trace_lines)
        line = MathTex(rf"{a} = {q} \times {b} + {r}").scale(0.6)
        line.move_to([TRACE_X, TRACE_Y0 - (n + 1) * TRACE_GAP, 0])
        self.trace_lines.append(line)

        if r > 0:
            highlight = Rectangle(
                width=self.rw + 0.06, height=self.rh + 0.06,
                color=GREY_A, stroke_width=3,
            )
            highlight.move_to([self.rx + self.rw / 2, self.ry + self.rh / 2, 0])
            c.play(Write(line), Create(highlight), p=ACTION_P, cap=2.0)
        else:
            # Nothing remains: point back at the squares that just finished it.
            last = self.carved_squares[-2:]
            c.play(
                Write(line),
                *(Indicate(sq, scale_factor=1.1, color=GCD_COLOR) for sq in last),
                p=ACTION_P, cap=2.2,
            )

    def show_gcd(self, c: BeatClock):
        self.gcd_stamp = MathTex(r"\text{gcd} = 6", color=GCD_COLOR).scale(1.2)
        self.gcd_stamp.move_to([0, HEADLINE_Y, 0])
        c.play(Write(self.gcd_stamp), p=ACTION_P, cap=2.0)

    def emphasize_squares(self, c: BeatClock):
        c.play(
            Indicate(VGroup(*self.carved_squares), scale_factor=1.05, color=GCD_COLOR),
            p=ACTION_P, cap=2.0,
        )

    def clear_decomposition(self, c: BeatClock):
        c.play(FadeOut(VGroup(*self.carved_squares)), p=ACTION_P, cap=1.8)

    def show_grid(self, c: BeatClock):
        cols, rows = 8, 3
        cell = RECT_W / cols  # == 6 * SCALE
        cells = [
            self.make_square(cell, GCD_COLOR).move_to(
                [RECT_X0 + cell * (col + 0.5), RECT_Y0 + cell * (row + 0.5), 0]
            )
            for row in range(rows)
            for col in range(cols)
        ]
        self.grid = VGroup(*cells)
        c.play(
            LaggedStart(*(GrowFromCenter(cell) for cell in cells), lag_ratio=0.04),
            p=ACTION_P, cap=3.0,
        )

    def emphasize_grid(self, c: BeatClock):
        c.play(Indicate(self.grid, scale_factor=1.03, color=GCD_COLOR), p=ACTION_P, cap=2.0)

    def show_toobig(self, c: BeatClock):
        """A 9x9 attempt: fits 18 exactly but not 48, leaving a visible gap."""
        size9 = 9 * SCALE
        rows, cols = 2, 5  # 18 / 9 = 2 exactly; floor(48 / 9) = 5
        squares = [
            self.make_square(size9, RED).move_to(
                [RECT_X0 + size9 * (col + 0.5), RECT_Y0 + size9 * (row + 0.5), 0]
            )
            for row in range(rows)
            for col in range(cols)
        ]
        leftover_w = RECT_W - cols * size9
        leftover = Rectangle(width=leftover_w, height=RECT_H, stroke_width=3, color=RED)
        leftover.move_to([RECT_X0 + cols * size9 + leftover_w / 2, RECT_Y0 + RECT_H / 2, 0])
        gap_label = Text("gap", color=RED).scale(0.35).next_to(leftover, DOWN, buff=0.15)

        self.toobig_group = VGroup(*squares, leftover, gap_label)
        c.play(FadeOut(self.grid), FadeIn(self.toobig_group), p=ACTION_P, cap=2.4)

    def emphasize_trace(self, c: BeatClock):
        group = VGroup(self.trace_heading, *self.trace_lines)
        c.play(Circumscribe(group, color=GREY_A, buff=0.15), p=ACTION_P, cap=2.0)

    def show_complexity(self, c: BeatClock):
        self.formula = MathTex(r"O(\log n)", color=NEUTRAL_COLOR).scale(1.1)
        self.formula.move_to([0, FORMULA_Y, 0])
        c.play(FadeOut(self.toobig_group), Write(self.formula), p=ACTION_P, cap=2.2)

    def show_contrast(self, c: BeatClock):
        new = MathTex(r"O(\log n) \;\text{vs}\; O(n)").scale(0.85).move_to([0, FORMULA_Y, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def show_fraction(self, c: BeatClock):
        # Inline slash, not \frac{}{}: the stacked form is tall enough to crowd
        # both the caption below and the gcd stamp above (see build_topic.py's
        # check_caption_band, which is what caught this).
        new = MathTex(r"48 / 18 = 8 / 3").scale(0.9).move_to([0, FORMULA_Y, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def clear_formula(self, c: BeatClock):
        c.play(FadeOut(self.formula), p=ACTION_P, cap=1.4)

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(
                VGroup(
                    self.title, self.goal_badge, self.rule_group,
                    self.boundary, self.dim_labels,
                    self.trace_heading, VGroup(*self.trace_lines),
                    self.gcd_stamp,
                )
            ),
            p=ACTION_P, cap=2.4,
        )
