"""The derivative of f(x) = x^2 at x = 1, as the limit of secant slopes.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/derivative.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption first.

Left: the curve, the fixed point P = (1, 1), a second point Q = (1+h, f(1+h)),
the run (h) and rise legs, and the secant through P and Q. All of those are
driven by one ValueTracker, so shrinking h rotates the secant continuously.
Right: the slope formula and a table of h, rise and slope. Forward difference,
so the slope is exactly 2 + h: 3, 2.5, 2.25, 2.1.

The brief stops h at 0.1, but a secant only *becomes* the tangent in the limit,
so one extra beat takes h to 0.001 (visually indistinguishable from the tangent)
before the line is relabelled as the tangent. Division by h means the tracker
can never actually reach 0.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

X0 = 1.0
H_STEPS = (1.0, 0.5, 0.25, 0.1)
H_LIMIT = 0.001

X_RANGE = (-0.5, 2.5)
Y_RANGE = (-1.0, 4.5)
AXES_CENTER = (-3.3, 0.55, 0)
# Lines are clipped to this box so they never leave the axes.
DRAW_X = (-0.4, 2.45)
DRAW_Y = (-0.9, 4.4)

PANEL_X = 3.9
FORMULA_Y = 2.2
COLS = (2.3, 3.9, 5.5)
HEADER_Y = 1.2
ROW_Y = (0.6, 0.15, -0.3, -0.75, -1.2)  # four h steps, then the limit row

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

CURVE_COLOR = BLUE
P_COLOR = WHITE
SECANT_COLOR = ORANGE
TANGENT_COLOR = GREEN
RUN_COLOR = YELLOW
RISE_COLOR = TEAL

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_curve", "draw_curve", ()),
    ("intro_steep", "sweep_curve", ()),
    ("intro_point", "show_p", ()),
    ("intro_rise_run", "show_rise_run", ()),

    ("setup_q", "show_q", ()),
    ("setup_h", "show_run", ()),
    ("setup_secant", "show_secant", ()),
    ("setup_formula", "show_slope_formula", ()),

    ("h1_value", "first_row", ()),
    ("h1_slope", "state_slope", (0,)),
    ("h2_shrink", "shrink", (1,)),
    ("h2_slope", "state_slope", (1,)),
    ("h3_shrink", "shrink", (2,)),
    ("h3_slope", "state_slope", (2,)),
    ("h4_shrink", "shrink", (3,)),
    ("h4_slope", "state_slope", (3,)),

    ("an_pattern", "sweep_rows", ()),
    ("an_expand", "set_formula", (r"\frac{(1+h)^2 - 1}{h} = \frac{1 + 2h + h^2 - 1}{h}",)),
    ("an_cancel", "set_formula", (r"\frac{2h + h^2}{h} = 2 + h",)),

    ("lim_shrink", "shrink_to_limit", ()),
    ("lim_tangent", "become_tangent", ()),
    ("lim_value", "set_formula", (r"f'(1) = 2", TANGENT_COLOR, 1.1)),
    ("an_meaning", "show_tangent_steps", ()),
    ("an_def", "set_formula", (r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}", WHITE, 0.72)),
    ("end_general", "set_formula", (r"f(x) = x^2 \;\Longrightarrow\; f'(x) = 2x", TANGENT_COLOR, 0.85)),
    ("end_line", "fade_out", ()),
]


def f(x: float) -> float:
    return x * x


def secant_slope(h: float) -> float:
    return (f(X0 + h) - f(X0)) / h


def fmt(v: float) -> str:
    return f"{v:g}"


class Derivative(TimedScene):
    TOPIC = "derivative"
    STATUS_AT = DOWN * 2.35

    def construct(self):
        self.setup_timing()
        self.h = ValueTracker(H_STEPS[0])
        self.rows: list[dict[str, Mobject]] = [{} for _ in ROW_Y]
        self.formula = None
        self.tangent_label = None
        self.tangent_steps = None

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
        self.title = Text("The Derivative", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

        self.axes = Axes(
            x_range=[*X_RANGE, 0.5],
            y_range=[*Y_RANGE, 1],
            x_length=6.0,
            y_length=4.2,
            tips=False,
            axis_config={"color": GREY_C, "stroke_width": 2},
            x_axis_config={
                "numbers_to_include": [1, 2], "font_size": 24,
                "decimal_number_config": {"num_decimal_places": 0},
            },
            y_axis_config={"numbers_to_include": [1, 2, 3, 4], "font_size": 24},
        ).move_to(AXES_CENTER)
        ax = self.axes

        self.curve = ax.plot(f, x_range=[X_RANGE[0], np.sqrt(DRAW_Y[1])], color=CURVE_COLOR, stroke_width=5)
        # Right of the y-axis (its tick numbers sit at x < 0) and well left of the curve's top.
        self.curve_label = MathTex(r"f(x) = x^2", color=CURVE_COLOR).scale(0.7).move_to(ax.c2p(0.8, 3.8))

        self.p_dot = Dot(ax.c2p(X0, f(X0)), radius=0.08, color=P_COLOR)
        self.p_label = MathTex(r"(1,\ 1)").scale(0.6).next_to(self.p_dot, UL, buff=0.08)

        def q_point():
            h = self.h.get_value()
            return ax.c2p(X0 + h, f(X0 + h))

        def corner():
            return ax.c2p(X0 + self.h.get_value(), f(X0))

        self.q_dot = always_redraw(lambda: Dot(q_point(), radius=0.08, color=SECANT_COLOR))
        self.run = always_redraw(lambda: Line(self.p_dot.get_center(), corner(), color=RUN_COLOR, stroke_width=4))
        self.rise = always_redraw(lambda: Line(corner(), q_point(), color=RISE_COLOR, stroke_width=4))
        self.secant = always_redraw(lambda: self.line_through_p(secant_slope(self.h.get_value()), SECANT_COLOR))
        # Built once and moved, not redrawn: re-typesetting MathTex every frame is slow.
        self.h_label = MathTex("h", color=RUN_COLOR).scale(0.6)
        self.h_label.add_updater(lambda m: m.next_to(self.run, DOWN, buff=0.1))

        header = VGroup(*(
            MathTex(tex, color=GREY_B).scale(0.65).move_to([x, HEADER_Y, 0])
            for tex, x in zip((r"h", r"\text{rise}", r"\text{slope}"), COLS)
        ))
        rule = Line([COLS[0] - 0.7, HEADER_Y - 0.25, 0], [COLS[-1] + 0.7, HEADER_Y - 0.25, 0], color=GREY_D, stroke_width=2)
        self.table_head = VGroup(header, rule)

    def line_through_p(self, m: float, colour) -> Line:
        """y = f(X0) + m (x - X0), clipped to the drawing box (m > 0 throughout)."""
        y0 = f(X0)
        x_lo = max(DRAW_X[0], X0 + (DRAW_Y[0] - y0) / m)
        x_hi = min(DRAW_X[1], X0 + (DRAW_Y[1] - y0) / m)
        return Line(
            self.axes.c2p(x_lo, y0 + m * (x_lo - X0)),
            self.axes.c2p(x_hi, y0 + m * (x_hi - X0)),
            color=colour, stroke_width=4,
        )

    def cell(self, tex: str, row: int, col: int, colour=WHITE) -> MathTex:
        mob = MathTex(tex, color=colour).scale(0.65).move_to([COLS[col], ROW_Y[row], 0])
        self.rows[row][col] = mob
        return mob

    def formula_tex(self, tex: str, colour=WHITE, scale: float = 0.8) -> MathTex:
        return MathTex(tex, color=colour).scale(scale).move_to([PANEL_X, FORMULA_Y, 0])

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def draw_curve(self, c: BeatClock):
        c.play(
            LaggedStart(Create(self.axes), Create(self.curve), FadeIn(self.curve_label), lag_ratio=0.35),
            p=ACTION_P,
            cap=2.4,
        )

    def sweep_curve(self, c: BeatClock):
        c.play(ShowPassingFlash(self.curve.copy().set_stroke(YELLOW, width=9), time_width=0.4), p=ACTION_P, cap=1.8)

    def show_p(self, c: BeatClock):
        c.play(GrowFromCenter(self.p_dot), FadeIn(self.p_label, shift=DOWN * 0.15), p=ACTION_P, cap=1.4)

    def show_rise_run(self, c: BeatClock):
        self.formula = self.formula_tex(r"\text{slope} = \frac{\text{rise}}{\text{run}}")
        c.play(Write(self.formula), p=ACTION_P, cap=1.6)

    def show_q(self, c: BeatClock):
        c.play(GrowFromCenter(self.q_dot), p=ACTION_P, cap=1.2)

    def show_run(self, c: BeatClock):
        c.play(Create(self.run), FadeIn(self.h_label), p=ACTION_P, cap=1.4)

    def show_secant(self, c: BeatClock):
        c.play(Create(self.secant), p=ACTION_P, cap=1.6)

    def show_slope_formula(self, c: BeatClock):
        nxt = self.formula_tex(r"\text{slope} = \frac{f(1+h) - f(1)}{h}")
        c.play(Create(self.rise), FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.8)
        self.formula = nxt

    def first_row(self, c: BeatClock):
        c.play(
            FadeIn(self.table_head),
            FadeIn(self.cell(fmt(H_STEPS[0]), 0, 0, RUN_COLOR)),
            Indicate(self.q_dot, scale_factor=1.6, color=SECANT_COLOR),
            p=ACTION_P,
            cap=1.6,
        )

    def shrink(self, c: BeatClock, row: int):
        """Move h to the next step; the secant, Q and both legs follow the tracker."""
        h = H_STEPS[row]
        c.play(
            self.h.animate.set_value(h),
            FadeIn(self.cell(fmt(h), row, 0, RUN_COLOR)),
            p=ACTION_P,
            cap=2.2,
        )

    def state_slope(self, c: BeatClock, row: int):
        h = H_STEPS[row]
        rise = f(X0 + h) - f(X0)
        c.play(
            Write(self.cell(fmt(round(rise, 6)), row, 1, RISE_COLOR)),
            Write(self.cell(fmt(round(secant_slope(h), 6)), row, 2, SECANT_COLOR)),
            p=ACTION_P,
            cap=1.6,
        )

    def sweep_rows(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(
                    Indicate(VGroup(self.rows[r][0], self.rows[r][2]), scale_factor=1.2, color=YELLOW)
                    for r in range(len(H_STEPS))
                ),
                lag_ratio=0.35,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def set_formula(self, c: BeatClock, tex: str, colour=WHITE, scale: float = 0.8):
        nxt = self.formula_tex(tex, colour, scale)
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.8)
        self.formula = nxt

    def shrink_to_limit(self, c: BeatClock):
        row = len(H_STEPS)
        c.play(
            self.h.animate.set_value(H_LIMIT),
            FadeIn(self.cell(r"h \to 0", row, 0, RUN_COLOR)),
            FadeIn(self.cell(r"\to 2", row, 2, TANGENT_COLOR)),
            p=ACTION_P + 0.1,
            cap=2.6,
        )

    def become_tangent(self, c: BeatClock):
        # Freeze the secant where it is (slope 2.001) and recolour it in place.
        self.secant.clear_updaters()
        self.h_label.clear_updaters()
        end = self.secant.get_end()
        self.tangent_label = Text("tangent", color=TANGENT_COLOR).scale(0.42).next_to(end, DR, buff=0.08)
        c.play(
            self.secant.animate.set_color(TANGENT_COLOR),
            FadeOut(VGroup(self.q_dot, self.run, self.rise, self.h_label)),
            FadeIn(self.tangent_label),
            p=ACTION_P,
            cap=1.6,
        )

    def show_tangent_steps(self, c: BeatClock):
        """One across, two up, along the tangent itself."""
        ax = self.axes
        corner = ax.c2p(X0 + 1, f(X0))
        top = ax.c2p(X0 + 1, f(X0) + 2)
        across = DashedLine(self.p_dot.get_center(), corner, color=RUN_COLOR, stroke_width=4)
        up = DashedLine(corner, top, color=RISE_COLOR, stroke_width=4)
        self.tangent_steps = VGroup(
            across, up,
            MathTex("1", color=RUN_COLOR).scale(0.6).next_to(across, DOWN, buff=0.1),
            MathTex("2", color=RISE_COLOR).scale(0.6).next_to(up, RIGHT, buff=0.1),
        )
        c.play(Create(self.tangent_steps), p=ACTION_P, cap=1.8)

    def fade_out(self, c: BeatClock):
        table = VGroup(self.table_head, *(m for row in self.rows for m in row.values()))
        c.play(
            FadeOut(VGroup(self.axes, self.curve, self.curve_label, self.p_dot, self.p_label)),
            FadeOut(VGroup(self.secant, self.tangent_label, self.tangent_steps)),
            FadeOut(VGroup(self.title, self.formula, table)),
            p=ACTION_P,
            cap=2.0,
        )
