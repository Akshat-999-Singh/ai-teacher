"""Gradient descent on f(x, y) = x^2 + 4y^2 from (4, 1), one step per sentence.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/gradient_descent.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption first.
The brief, with its trace and rejected inputs, is scripts/gradient_descent.brief.md.

Deliberately not `newtons_method` or the derivative topics: nothing here is the
graph of a function and no tangent is drawn. The picture is a contour map seen
from above, at equal aspect so the gradient really does cross its ring at a
right angle. One start, three learning rates: 0.1 crawls along the valley floor,
0.2 zigzags but gets lower sooner, 0.3 leaps the valley and climbs. A loss chart
on the right grows one point per step, one line per run.

The red gradient arrow is a direction indicator drawn at 0.2 of its true length
(the true one is 11.3 units, wider than the map). The white step arrow is exact:
it ends where the dot will land. All three first steps lie along one line, so
trails are z-ordered shortest on top, which leaves every stopping point visible.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

K = 4                                   # f = x^2 + K y^2
START = (4.0, 1.0)
WINDOW_X, WINDOW_Y = (-2.5, 6.0), (-3.05, 3.05)
SCALE = 0.72
MAP_ORIGIN = np.array([-6.75 - WINDOW_X[0] * SCALE, 0.5, 0.0])   # screen point of world (0, 0)
RING_RADII = (1, 2, 3, 4, 5, 6, 7, 8)   # x semi-axis a; the ring is loss a^2
LABELLED = (1, 2, 3, 4, 5)
GRADIENT_DRAWN = 0.2                    # red arrow is this fraction of the true gradient

PANEL_X = 3.3
FORMULA_Y, RULE_Y, READOUT_Y = 2.45, 1.95, 1.45
CHART_AT = (PANEL_X, -0.3, 0)

RING_INNER, RING_OUTER = BLUE_D, GREY_B
MIN_COLOR = GREEN
UPHILL_COLOR = RED
STEP_COLOR = WHITE

# key: (learning rate, steps shown, colour, trail z)
RUNS = {
    "A": (0.1, 5, YELLOW, 5),
    "B": (0.2, 4, TEAL, 4),
    "C": (0.3, 3, RED, 3),
}

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_map", "draw_map", ()),
    ("intro_rings", "label_rings", ()),
    ("intro_min", "mark_min", ()),
    ("intro_formula", "write_formula", ()),
    ("intro_start", "place_start", ()),

    ("g_arrow", "grow_gradient", ()),
    ("g_perp", "right_angle", ()),
    ("g_flip", "flip", ()),
    ("g_scale", "shrink", ()),
    ("g_step", "first_step", ()),

    ("a_s2", "step", ("A", 2)),
    ("a_s3", "step", ("A", 3)),
    ("a_s4", "step", ("A", 4)),
    ("a_s5", "step", ("A", 5)),
    ("rule", "show_rule", ()),

    ("b_reset", "reset", ("B",)),
    ("b_s1", "step", ("B", 1)),
    ("b_s2", "step", ("B", 2)),
    ("b_s3", "step", ("B", 3)),
    ("b_s4", "step", ("B", 4)),

    ("c_reset", "reset", ("C",)),
    ("c_s1", "step", ("C", 1)),
    ("c_s2", "step", ("C", 2)),
    ("c_s3", "step", ("C", 3)),
    ("c_div", "diverge", ()),

    ("end_same", "same_map", ()),
    ("end_small", "spotlight", ("A",)),
    ("end_big", "spotlight", ("C",)),
    ("end_line", "fade_out", ()),
]


def loss(x: float, y: float) -> float:
    return x * x + K * y * y


def grad(x: float, y: float) -> tuple[float, float]:
    return 2 * x, 2 * K * y


def descend(rate: float, steps: int) -> list[tuple[float, float]]:
    pts = [START]
    for _ in range(steps):
        x, y = pts[-1]
        gx, gy = grad(x, y)
        pts.append((x - rate * gx, y - rate * gy))
    return pts


def w2s(x: float, y: float) -> np.ndarray:
    return MAP_ORIGIN + SCALE * np.array([x, y, 0.0])


class Run:
    """One learning rate: its points and what has been drawn for it. Not a Mobject."""

    def __init__(self, key: str):
        self.key = key
        self.rate, self.steps, self.color, self.z = RUNS[key]
        self.pts = descend(self.rate, self.steps)
        self.losses = [loss(*p) for p in self.pts]
        self.dot = None
        self.trail = VGroup()
        self.chart = VGroup()


class GradientDescent(TimedScene):
    TOPIC = "gradient_descent"
    STATUS_AT = DOWN * 2.35

    def construct(self):
        self.setup_timing()
        self.runs = {key: Run(key) for key in RUNS}
        self.arrow = None
        self.loss_readout = None
        self.rate_readout = None
        self.rule = None

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
        self.title = Text("Gradient Descent", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

        a, b = w2s(WINDOW_X[0], WINDOW_Y[0]), w2s(WINDOW_X[1], WINDOW_Y[1])
        self.map_frame = Rectangle(width=b[0] - a[0], height=b[1] - a[1], color=GREY_D, stroke_width=2)
        self.map_frame.move_to((a + b) / 2)

        self.rings = VGroup()
        for i, radius in enumerate(RING_RADII):
            color = interpolate_color(RING_INNER, RING_OUTER, i / (len(RING_RADII) - 1))
            self.rings.add(self.ring(radius, color))

        self.ring_labels = VGroup()
        t = 110 * DEGREES
        for radius in LABELLED:
            label = MathTex(str(radius * radius), color=GREY_A).scale(0.42)
            label.move_to(w2s(radius * np.cos(t), radius / np.sqrt(K) * np.sin(t)))
            label.add_background_rectangle(color=BLACK, opacity=1, buff=0.04)
            self.ring_labels.add(label)

        self.min_dot = Dot(w2s(0, 0), radius=0.07, color=MIN_COLOR).set_z_index(7)
        self.min_label = MathTex(r"\text{min}", color=MIN_COLOR).scale(0.45).next_to(self.min_dot, DOWN, buff=0.08)

        self.formula = MathTex(r"\text{loss} = x^2 + 4y^2").scale(0.65).move_to([PANEL_X, FORMULA_Y, 0])

        self.chart_axes = Axes(
            x_range=[0, 6, 1],
            y_range=[0, 32, 8],
            x_length=4.6,
            y_length=2.2,
            tips=False,
            axis_config={"color": GREY_C, "stroke_width": 2, "font_size": 20},
            x_axis_config={"numbers_to_include": [1, 2, 3, 4, 5]},
            y_axis_config={"numbers_to_include": [8, 16, 24, 32]},
        ).move_to(CHART_AT)
        x_end, y_end = self.chart_axes.c2p(6, 0), self.chart_axes.c2p(0, 32)
        self.chart_labels = VGroup(
            MathTex(r"\text{step}", color=GREY_B).scale(0.45).next_to(x_end, RIGHT, buff=0.12),
            MathTex(r"\text{loss}", color=GREY_B).scale(0.45).next_to(y_end, UP, buff=0.1),
        )

        # The chart's upper right is empty in every run: red stops at step 3.
        self.legend = {}
        for row, run in enumerate(self.runs.values()):
            swatch = Line(ORIGIN, RIGHT * 0.35, color=run.color, stroke_width=5)
            text = MathTex(rf"\text{{rate }} {run.rate}", color=run.color).scale(0.45).next_to(swatch, RIGHT, buff=0.1)
            entry = VGroup(swatch, text)
            entry.move_to(self.chart_axes.c2p(4.2, 30 - 5.5 * row), aligned_edge=LEFT)
            self.legend[run.key] = entry

    def ring(self, radius: float, color) -> VGroup:
        """The level set loss = radius^2, clipped to the map window, as one or more arcs."""
        # Start at the leftmost point: every ring the window clips is clipped there,
        # so no visible arc ever wraps around the end of the sample list.
        ts = np.linspace(PI, 3 * PI, 721)
        arcs, current = VGroup(), []
        for t in ts:
            x, y = radius * np.cos(t), radius / np.sqrt(K) * np.sin(t)
            inside = WINDOW_X[0] <= x <= WINDOW_X[1] and WINDOW_Y[0] <= y <= WINDOW_Y[1]
            if inside:
                current.append(w2s(x, y))
            if (not inside or t == ts[-1]) and len(current) > 1:
                arcs.add(VMobject(color=color, stroke_width=2.5).set_points_as_corners(current))
            if not inside:
                current = []
        return arcs

    def step_arrow(self, start, end, color=STEP_COLOR) -> Arrow:
        return Arrow(
            w2s(*start), w2s(*end), buff=0, color=color, stroke_width=5,
            max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10,
        ).set_z_index(6)

    def loss_text(self, value: float) -> MathTex:
        return MathTex(rf"\text{{loss}} = {value:.2f}").scale(0.6).move_to([PANEL_X + 1.4, READOUT_Y, 0])

    def rate_text(self, run: Run) -> MathTex:
        return MathTex(rf"\text{{rate}} = {run.rate}", color=run.color).scale(0.6).move_to([PANEL_X - 1.4, READOUT_Y, 0])

    def chart_point(self, run: Run, n: int) -> list[Animation]:
        """Chrome: the run's loss after n steps joins its chart line. Rides in the action's play."""
        at = self.chart_axes.c2p(n, run.losses[n])
        dot = Dot(at, radius=0.045, color=run.color).set_z_index(run.z)
        # FadeIn, not GrowFromCenter: inside step()'s lagged play a zero-scale dot
        # still renders as a speck while it waits for its half to begin.
        anims = [FadeIn(dot, scale=0.3)]
        if n:
            line = Line(self.chart_axes.c2p(n - 1, run.losses[n - 1]), at, color=run.color, stroke_width=3)
            line.set_z_index(run.z)
            run.chart.add(line)
            anims.insert(0, Create(line))
        run.chart.add(dot)
        return anims

    def swap_loss(self, value: float) -> Animation:
        """Crossfade, not FadeTransform: waiting in step()'s second half, a FadeTransform
        shows its target at full opacity on top of the old number."""
        new = self.loss_text(value)
        anim = AnimationGroup(FadeOut(self.loss_readout), FadeIn(new))
        self.loss_readout = new
        return anim

    def move(self, run: Run, n: int) -> list[Animation]:
        """Dot slides to point n, its trail segment draws, chart and readout follow."""
        seg = Line(w2s(*run.pts[n - 1]), w2s(*run.pts[n]), color=run.color, stroke_width=4).set_z_index(run.z)
        run.trail.add(seg)
        return [
            run.dot.animate.move_to(w2s(*run.pts[n])),
            Create(seg),
            *self.chart_point(run, n),
            self.swap_loss(run.losses[n]),
        ]

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def draw_map(self, c: BeatClock):
        c.play(
            Create(self.map_frame),
            LaggedStart(*(Create(ring) for ring in self.rings), lag_ratio=0.15),
            p=ACTION_P + 0.1,
            cap=2.6,
        )

    def label_rings(self, c: BeatClock):
        # Outside in, so the eye travels downhill with the sentence.
        c.play(LaggedStart(*(FadeIn(label) for label in reversed(self.ring_labels)), lag_ratio=0.3), p=ACTION_P, cap=2.2)

    def mark_min(self, c: BeatClock):
        c.play(
            GrowFromCenter(self.min_dot),
            Flash(self.min_dot, color=MIN_COLOR, flash_radius=0.3),
            FadeIn(self.min_label, shift=UP * 0.1),
            p=ACTION_P,
            cap=1.4,
        )

    def write_formula(self, c: BeatClock):
        c.play(Write(self.formula), p=ACTION_P, cap=1.8)

    def place_start(self, c: BeatClock):
        run = self.runs["A"]
        run.dot = Dot(w2s(*START), radius=0.09, color=run.color).set_z_index(8)
        self.loss_readout = self.loss_text(run.losses[0])
        c.play(
            GrowFromCenter(run.dot),
            Flash(run.dot, color=run.color, flash_radius=0.3),
            FadeIn(self.loss_readout),
            Create(self.chart_axes),
            FadeIn(self.chart_labels),
            *self.chart_point(run, 0),
            p=ACTION_P,
            cap=1.8,
        )

    def grow_gradient(self, c: BeatClock):
        gx, gy = grad(*START)
        tip = (START[0] + GRADIENT_DRAWN * gx, START[1] + GRADIENT_DRAWN * gy)
        self.arrow = self.step_arrow(START, tip, UPHILL_COLOR)
        self.grad_label = MathTex(rf"\text{{gradient }} ({gx:g},\, {gy:g})", color=UPHILL_COLOR).scale(0.5)
        self.grad_label.next_to(self.arrow.get_center(), UL, buff=0.12)
        self.grad_label.add_background_rectangle(color=BLACK, opacity=0.85, buff=0.05)
        c.play(GrowArrow(self.arrow), FadeIn(self.grad_label), p=ACTION_P, cap=1.6)

    def right_angle(self, c: BeatClock):
        level = np.sqrt(loss(*START))
        t0 = np.arctan2(START[1] * np.sqrt(K), START[0])
        arc = ParametricFunction(
            lambda t: w2s(level * np.cos(t), level / np.sqrt(K) * np.sin(t)),
            t_range=[t0 - 40 * DEGREES, t0 + 40 * DEGREES],
        )
        self.own_ring = DashedVMobject(arc, num_dashes=26).set_stroke(YELLOW_A, width=3)
        g = np.array([*grad(*START), 0.0])
        n = g / np.linalg.norm(g)
        t = np.array([n[1], -n[0], 0.0])
        p, s = w2s(*START), 0.2
        self.elbow = VMobject(color=WHITE, stroke_width=3).set_points_as_corners([p + s * t, p + s * t + s * n, p + s * n])
        self.elbow.set_z_index(7)
        c.play(Create(self.own_ring), Create(self.elbow), p=ACTION_P, cap=1.8)

    def flip(self, c: BeatClock):
        about = w2s(*START)
        start = self.arrow.copy()

        def turn(mob, alpha):
            mob.become(start.copy().rotate(alpha * PI, about_point=about))
            mob.set_color(interpolate_color(UPHILL_COLOR, STEP_COLOR, alpha))

        c.play(
            UpdateFromAlphaFunc(self.arrow, turn),
            FadeOut(self.grad_label),
            FadeOut(self.own_ring),
            FadeOut(self.elbow),
            p=ACTION_P,
            cap=1.8,
        )

    def shrink(self, c: BeatClock):
        run = self.runs["A"]
        self.rate_readout = self.rate_text(run)
        c.play(
            Transform(self.arrow, self.step_arrow(run.pts[0], run.pts[1])),
            FadeIn(self.rate_readout),
            FadeIn(self.legend[run.key]),
            p=ACTION_P,
            cap=1.6,
        )

    def first_step(self, c: BeatClock):
        c.play(*self.move(self.runs["A"], 1), p=ACTION_P, cap=1.8)

    def step(self, c: BeatClock, key: str, n: int):
        """Measure (the exact step arrow grows), then walk it. One play, two halves."""
        run = self.runs[key]
        retire = [FadeOut(self.arrow)] if self.arrow is not None else []
        self.arrow = self.step_arrow(run.pts[n - 1], run.pts[n])
        c.play(
            LaggedStart(
                AnimationGroup(*retire, GrowArrow(self.arrow)),
                AnimationGroup(*self.move(run, n)),
                lag_ratio=1.0,
            ),
            p=ACTION_P + 0.15,
            cap=2.6,
        )

    def show_rule(self, c: BeatClock):
        self.rule = MathTex(
            r"\text{new point} = \text{point} - \text{rate} \times \text{gradient}"
        ).scale(0.55).move_to([PANEL_X, RULE_Y, 0])
        arrow, self.arrow = self.arrow, None
        c.play(Write(self.rule), FadeOut(arrow), p=ACTION_P, cap=2.0)

    def reset(self, c: BeatClock, key: str):
        run = self.runs[key]
        run.dot = Dot(w2s(*START), radius=0.09, color=run.color).set_z_index(8)
        dim = []
        for other in self.runs.values():
            if other is not run and other.dot is not None:
                dim += [other.trail.animate.set_stroke(opacity=0.35), other.dot.animate.set_fill(opacity=0.35)]
        retire = [FadeOut(self.arrow)] if self.arrow is not None else []
        self.arrow = None
        new_rate = self.rate_text(run)
        c.play(
            *dim,
            *retire,
            GrowFromCenter(run.dot),
            FadeTransform(self.rate_readout, new_rate),
            self.swap_loss(run.losses[0]),
            FadeIn(self.legend[key]),
            *self.chart_point(run, 0),
            p=ACTION_P,
            cap=1.8,
        )
        self.rate_readout = new_rate

    def diverge(self, c: BeatClock):
        run = self.runs["C"]
        c.play(
            Circumscribe(self.loss_readout, color=run.color, buff=0.08),
            Flash(run.dot, color=run.color, flash_radius=0.35),
            p=ACTION_P,
            cap=1.8,
        )

    def same_map(self, c: BeatClock):
        arrow, self.arrow = self.arrow, None
        legend = VGroup(*self.legend.values())
        c.play(FadeOut(arrow), Circumscribe(legend, color=GREY_A, buff=0.08), p=ACTION_P, cap=1.8)

    def spotlight(self, c: BeatClock, key: str):
        anims = []
        for run in self.runs.values():
            opacity, width = (1.0, 7) if run.key == key else (0.2, 4)
            # All three first steps share one line; the run being named goes on top.
            run.trail.set_z_index(7 if run.key == key else run.z)
            anims += [
                run.trail.animate.set_stroke(opacity=opacity, width=width),
                run.dot.animate.set_fill(opacity=opacity),
            ]
        c.play(*anims, Indicate(self.legend[key], scale_factor=1.2, color=self.runs[key].color), p=ACTION_P, cap=1.8)

    def fade_out(self, c: BeatClock):
        # Listed by hand: the dry-run probe has no self.mobjects to sweep.
        everything = VGroup(
            self.title, self.map_frame, self.rings, self.ring_labels, self.min_dot, self.min_label,
            self.formula, self.rule, self.rate_readout, self.loss_readout,
            self.chart_axes, self.chart_labels, *self.legend.values(),
            *(VGroup(run.trail, run.dot, run.chart) for run in self.runs.values()),
        )
        c.play(FadeOut(everything), p=ACTION_P, cap=2.0)
