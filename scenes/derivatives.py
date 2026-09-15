"""The derivative as a function: a sliding tangent draws the slope graph.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/derivatives.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption first.

Deliberately a different teaching moment from `derivative` (the slope at ONE
point, as a limit of secants): here the point of tangency travels the whole
curve f(x) = x^3/3 - x, and a dot on a second axes underneath records the
tangent's slope at every x, tracing f'(x) = x^2 - 1. The payoff is that the
hill (x = -1) and the valley (x = 1) line up with the zeros of the slope graph.

Input choice (see scripts/derivatives.brief.md): x^2 and x^3 put their flat
tangent along the x-axis, x^3 never has a negative slope, x^3 - 3x breaks the
layout budget (slope 9), sin x has unsayable slopes. x^3/3 - x gives slopes
3, 0, -1, 0, 3 at the five stops and fits the top graph at equal aspect, so the
tangent's drawn tilt is its true slope.

One ValueTracker (self.x) drives the point, tangent, guide, slope dot, trail
and readout. The trail is a plot redrawn from -2 to the current x, not a
TracedPath, so it is exactly f' whatever the frame rate.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

X_START, X_END = -2.0, 2.0
X_RANGE = (-2.5, 2.5)
X_UNIT = 1.3
X_LENGTH = X_UNIT * (X_RANGE[1] - X_RANGE[0])
GRAPH_CX = -2.5

TOP_Y_RANGE = (-1.0, 1.0)
TOP_CY = 1.45                     # equal aspect: 1.3 scene units per unit on both axes
BOT_Y_RANGE = (-1.5, 3.5)
BOT_Y_LENGTH = 2.6
BOT_TOP = -0.35

TAN_LEN = 1.2
# Axes.plot otherwise samples at the axis tick step (1), which bends x^2 - 1 visibly.
PLOT_STEP = 0.02
PANEL_X = 4.3
CURVE_LABEL_Y = 2.35
READOUT_Y = 1.35
SLOPE_LABEL_Y = -0.9
FORMULA_Y = -1.75

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

CURVE_COLOR = BLUE
TANGENT_COLOR = YELLOW
SLOPE_COLOR = PURPLE_B
POS_COLOR = GREEN
NEG_COLOR = RED
ZERO_COLOR = GOLD
GUIDE_COLOR = PURPLE_A   # not grey: at x = 0 a grey guide vanishes into both grey y-axes

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_curve", "draw_curve", ()),
    ("intro_shape", "label_shape", ()),
    ("intro_point", "show_point", ()),
    ("intro_tangent", "show_tangent", ()),
    ("intro_slope", "show_readout", ()),

    ("setup_axes", "show_slope_axes", ()),
    ("setup_guide", "show_guide", ()),
    ("setup_dot", "show_slope_dot", ()),

    ("s1_slide", "slide", (-1.0,)),
    ("s1_flat", "flag_flat", ()),
    ("s1_zero", "flash_dot", (ZERO_COLOR,)),
    ("s1_link", "link_zero", (-1.0,)),

    ("s2_slide", "slide", (0.0,)),
    ("s2_negative", "indicate_dot", (NEG_COLOR,)),
    ("s2_bottom", "flash_dot", (NEG_COLOR,)),

    ("s3_slide", "slide", (1.0,)),
    ("s3_flat", "flag_flat", ()),
    ("s3_link", "link_zero", (1.0,)),

    ("s4_slide", "slide", (2.0,)),
    ("s4_positive", "indicate_dot", (POS_COLOR,)),

    ("an_trace", "reveal_slope_graph", ()),
    ("an_formula", "set_formula", (r"f'(x) = x^2 - 1",)),
    ("an_check", "check_formula", ()),
    ("an_up", "shade_sign", (True,)),
    ("an_down", "shade_sign", (False,)),
    ("an_turn", "pulse_zeros", ()),

    ("end_general", "frame_function", ()),
    ("end_line", "fade_out", ()),
]


def f(x: float) -> float:
    return x ** 3 / 3 - x


def fp(x: float) -> float:
    return x * x - 1


def sign_color(m: float):
    if abs(m) < 0.005:
        return ZERO_COLOR
    return POS_COLOR if m > 0 else NEG_COLOR


class Derivatives(TimedScene):
    TOPIC = "derivatives"
    STATUS_AT = DOWN * 3.45

    def construct(self):
        self.setup_timing()
        self.x = ValueTracker(X_START)
        self.formula = None
        self.links = VGroup()
        self.rings = VGroup()
        self.shading = VGroup()
        self.overlays = VGroup()
        self.slope_graph = None
        self.frame_box = None

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
        self.title = Text("The Derivative as a Function", weight=BOLD).scale(0.75).to_edge(UP, buff=0.3)
        self.add(self.title)

        axis_style = {"color": GREY_C, "stroke_width": 2}
        self.top_axes = Axes(
            x_range=[*X_RANGE, 1],
            y_range=[*TOP_Y_RANGE, 1],
            x_length=X_LENGTH,
            y_length=X_UNIT * (TOP_Y_RANGE[1] - TOP_Y_RANGE[0]),
            tips=False,
            axis_config=axis_style,
            x_axis_config={"numbers_to_include": [-2, -1, 1, 2], "font_size": 22},
        )
        # Place by the origin, not the bounding box, so both axes share one x mapping.
        self.top_axes.shift([GRAPH_CX, TOP_CY, 0] - self.top_axes.c2p(0, 0))
        top = self.top_axes
        # The hill link and the x = 2 guide cross the tick numbers: give them a black patch drawn
        # over dashed lines, with the curve and tangent at a higher z so only lines are cut.
        for number in top.x_axis.numbers:
            number.add_background_rectangle(color=BLACK, opacity=1, buff=0.03)
            number.set_z_index(1)

        self.bot_axes = Axes(
            x_range=[*X_RANGE, 1],
            y_range=[*BOT_Y_RANGE, 1],
            x_length=X_LENGTH,
            y_length=BOT_Y_LENGTH,
            tips=False,
            axis_config=axis_style,
            # No -1 label: the slope dot and graph pass over it at f'(0) = -1.
            y_axis_config={"numbers_to_include": [1, 2, 3], "font_size": 22},
        )
        bot_origin_y = BOT_TOP - BOT_Y_LENGTH * (BOT_Y_RANGE[1] - 0) / (BOT_Y_RANGE[1] - BOT_Y_RANGE[0])
        self.bot_axes.shift([GRAPH_CX, bot_origin_y, 0] - self.bot_axes.c2p(0, 0))
        bot = self.bot_axes

        self.curve = top.plot(f, x_range=[X_START, X_END, PLOT_STEP], color=CURVE_COLOR, stroke_width=5).set_z_index(1)
        self.curve_label = MathTex(r"f(x) = \frac{x^3}{3} - x", color=CURVE_COLOR).scale(0.75)
        self.curve_label.move_to([PANEL_X, CURVE_LABEL_Y, 0])

        self.hill_label = Text("hill", color=GREY_A).scale(0.4).next_to(top.c2p(-1, f(-1)), UP, buff=0.32)
        self.valley_label = Text("valley", color=GREY_A).scale(0.4).next_to(top.c2p(1, f(1)), DOWN, buff=0.3).shift(RIGHT * 0.65)  # off the gold link at x = 1

        # MathTex, not Text: Text kerned "of f" into "off".
        self.bot_label = MathTex(r"\text{slope of } f", color=SLOPE_COLOR).scale(0.7)
        self.bot_label.move_to([PANEL_X, SLOPE_LABEL_Y, 0])

        def point():
            x = self.x.get_value()
            return top.c2p(x, f(x))

        def slope_point():
            x = self.x.get_value()
            return bot.c2p(x, fp(x))

        def tangent():
            x = self.x.get_value()
            direction = np.array([1.0, fp(x), 0.0])
            direction /= np.linalg.norm(direction)
            c = point()
            return Line(c - direction * TAN_LEN / 2, c + direction * TAN_LEN / 2,
                        color=TANGENT_COLOR, stroke_width=5).set_z_index(2)

        def trail():
            x = max(self.x.get_value(), X_START + 1e-3)
            return bot.plot(fp, x_range=[X_START, x, PLOT_STEP], color=SLOPE_COLOR, stroke_width=4)

        self.point_dot = always_redraw(lambda: Dot(point(), radius=0.08, color=TANGENT_COLOR).set_z_index(2))
        self.tangent = always_redraw(tangent)
        self.guide = always_redraw(lambda: DashedLine(point(), slope_point(), color=GUIDE_COLOR,
                                                      stroke_width=2, dash_length=0.1))
        self.slope_dot = always_redraw(lambda: Dot(slope_point(), radius=0.09, color=SLOPE_COLOR))
        self.trail = always_redraw(trail)

        # Built once and updated, not re-typeset from scratch every frame.
        self.readout_label = MathTex(r"\text{slope} =").scale(0.75)
        self.readout_value = DecimalNumber(fp(X_START), num_decimal_places=2, include_sign=False).scale(0.75)
        self.readout = VGroup(self.readout_label, self.readout_value)
        self.readout_label.move_to([PANEL_X - 0.55, READOUT_Y, 0])
        self.readout_value.next_to(self.readout_label, RIGHT, buff=0.2)
        self.readout_value.set_color(sign_color(fp(X_START)))

        def update_readout(m):
            slope = round(fp(self.x.get_value()), 2) + 0.0  # +0.0 turns -0.0 into 0.0
            m.set_value(slope)
            m.next_to(self.readout_label, RIGHT, buff=0.2)
            m.set_color(sign_color(slope))

        self.readout_value.add_updater(update_readout)

    def formula_tex(self, tex: str, colour=WHITE, scale: float = 0.75) -> MathTex:
        return MathTex(tex, color=colour).scale(scale).move_to([PANEL_X, FORMULA_Y, 0])

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def draw_curve(self, c: BeatClock):
        c.play(
            LaggedStart(Create(self.top_axes), Create(self.curve), FadeIn(self.curve_label), lag_ratio=0.35),
            p=ACTION_P,
            cap=2.4,
        )

    def label_shape(self, c: BeatClock):
        c.play(
            LaggedStart(FadeIn(self.hill_label, shift=DOWN * 0.15),
                        FadeIn(self.valley_label, shift=UP * 0.15), lag_ratio=0.5),
            p=ACTION_P,
            cap=1.8,
        )

    def show_point(self, c: BeatClock):
        c.play(GrowFromCenter(self.point_dot), p=ACTION_P, cap=1.2)

    def show_tangent(self, c: BeatClock):
        c.play(Create(self.tangent), p=ACTION_P, cap=1.6)

    def show_readout(self, c: BeatClock):
        c.play(FadeIn(self.readout, shift=LEFT * 0.2), p=ACTION_P, cap=1.4)

    def show_slope_axes(self, c: BeatClock):
        c.play(Create(self.bot_axes), FadeIn(self.bot_label), p=ACTION_P, cap=2.0)

    def show_guide(self, c: BeatClock):
        c.play(Create(self.guide), p=ACTION_P, cap=1.6)

    def show_slope_dot(self, c: BeatClock):
        self.add(self.trail)  # empty until x moves; drawn under the dot
        c.play(GrowFromCenter(self.slope_dot), p=ACTION_P, cap=1.2)

    def slide(self, c: BeatClock, to_x: float):
        """Move the point of tangency; everything else follows the tracker."""
        c.play(self.x.animate.set_value(to_x), p=ACTION_P + 0.15, cap=3.0, rate_func=smooth)

    def flag_flat(self, c: BeatClock):
        c.play(Indicate(self.tangent, scale_factor=1.3, color=ZERO_COLOR), p=ACTION_P, cap=1.6)

    def flash_dot(self, c: BeatClock, colour):
        c.play(Flash(self.slope_dot.get_center(), color=colour, line_length=0.2, num_lines=10),
               p=ACTION_P, cap=1.4)

    def indicate_dot(self, c: BeatClock, colour):
        c.play(
            Indicate(self.slope_dot, scale_factor=1.8, color=colour),
            Indicate(self.readout_value, scale_factor=1.2, color=colour),
            p=ACTION_P,
            cap=1.6,
        )

    def link_zero(self, c: BeatClock, x: float):
        """Freeze the turning point and its zero together: gold link, a ring at each end."""
        above = self.top_axes.c2p(x, f(x))
        below = self.bot_axes.c2p(x, 0)
        link = DashedLine(above, below, color=ZERO_COLOR, stroke_width=3, dash_length=0.12)
        rings = VGroup(Circle(radius=0.16, color=ZERO_COLOR, stroke_width=4).move_to(above),
                       Circle(radius=0.16, color=ZERO_COLOR, stroke_width=4).move_to(below))
        self.links.add(link)
        self.rings.add(*rings)
        c.play(Create(link), Create(rings), p=ACTION_P, cap=1.8)

    def reveal_slope_graph(self, c: BeatClock):
        """Retire the moving probe and draw the finished slope graph over its trail."""
        for mob in (self.point_dot, self.tangent, self.guide, self.slope_dot, self.trail):
            mob.clear_updaters()
        self.readout_value.clear_updaters()
        self.slope_graph = self.bot_axes.plot(fp, x_range=[X_START, X_END, PLOT_STEP], color=SLOPE_COLOR, stroke_width=6)
        c.play(
            # The trail fades inside this play rather than via self.remove(): the build
            # checks' dry-run probe stubs play/wait/add but not remove, so remove() crashes it.
            FadeOut(VGroup(self.point_dot, self.tangent, self.guide, self.slope_dot, self.readout, self.trail)),
            Create(self.slope_graph),
            p=ACTION_P,
            cap=2.0,
        )

    def set_formula(self, c: BeatClock, tex: str):
        nxt = self.formula_tex(tex, SLOPE_COLOR)
        if self.formula is None:
            c.play(Write(nxt), p=ACTION_P, cap=1.6)
        else:
            c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.6)
        self.formula = nxt

    def check_formula(self, c: BeatClock):
        nxt = self.formula_tex(r"f'(1) = 1^2 - 1 = 0", ZERO_COLOR)
        c.play(
            FadeTransform(self.formula, nxt),
            Indicate(self.rings[3], scale_factor=1.5, color=ZERO_COLOR),
            p=ACTION_P,
            cap=1.8,
        )
        self.formula = nxt

    def shade_sign(self, c: BeatClock, positive: bool):
        colour = POS_COLOR if positive else NEG_COLOR
        spans = [(X_START, -1.0), (1.0, X_END)] if positive else [(-1.0, 1.0)]
        areas = VGroup(*(
            self.bot_axes.get_area(self.slope_graph, x_range=span, color=colour, opacity=0.35).set_z_index(-1)  # under the slope graph
            for span in spans
        ))
        overlays = VGroup(*(
            self.top_axes.plot(f, x_range=[*span, PLOT_STEP], color=colour, stroke_width=6).set_z_index(1) for span in spans
        ))
        self.shading.add(*areas)
        self.overlays.add(*overlays)
        c.play(FadeIn(areas), Create(overlays), p=ACTION_P, cap=1.8)

    def pulse_zeros(self, c: BeatClock):
        c.play(
            LaggedStart(*(Indicate(ring, scale_factor=1.6, color=WHITE) for ring in self.rings), lag_ratio=0.2),
            p=ACTION_P,
            cap=2.0,
        )

    def frame_function(self, c: BeatClock):
        self.frame_box = SurroundingRectangle(
            VGroup(self.bot_axes, self.slope_graph), color=SLOPE_COLOR, buff=0.08, corner_radius=0.1
        )
        c.play(Create(self.frame_box), Indicate(self.bot_label, color=SLOPE_COLOR), p=ACTION_P, cap=1.8)

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(self.top_axes, self.curve, self.overlays, self.curve_label,
                           self.hill_label, self.valley_label)),
            FadeOut(VGroup(self.bot_axes, self.slope_graph, self.shading, self.bot_label, self.frame_box)),
            FadeOut(VGroup(self.links, self.rings, self.formula, self.title)),
            p=ACTION_P,
            cap=2.0,
        )
