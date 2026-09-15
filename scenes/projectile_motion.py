"""Projectile motion, animated one narration sentence at a time.

Same contract as bubble_sort / binary_search / euclidean_gcd: every entry in
SCRIPT pairs a beat name from scripts/projectile_motion.json with the single
visible action that sentence describes, and `self.beat(name)` writes the
sentence as the caption before the action runs. See scenes/beat_timing.py.

Traced before writing any narration (v0 = 20 m/s, angle = 30 deg, g = 10):
  vx = 20 cos(30) = 10 sqrt(3) = 17.3205... m/s
  vy = 20 sin(30) = 10 m/s                          (clean)
  t_apex  = vy / g           = 1 s                  (clean)
  t_total = 2 vy / g         = 2 s                  (clean)
  h_max   = vy^2 / (2g)      = 5 m                   (clean)
  range   = vx * t_total     = 20 sqrt(3) = 34.641... m
vy, both times and h_max land on clean integers; vx and range are multiples
of sqrt(3) and do not. 30 degrees is kept as specified rather than swapped
for a angle that clears -- vx and range are shown on screen rounded to one
decimal place (17.3 m/s, 34.6 m), which is standard practice, not a silent
change of the problem.

The teaching point (horizontal and vertical motion are independent) is shown,
not just asserted: the ground shadow's x always equals the real ball's x, and
the height shadow's y always equals the real ball's y, by construction of
shadow_pt()/vert_pt() below -- each shadow literally isolates one coordinate
of the same flight.

Run tools/build_topic.py first; without measured timings the beats fall back
to FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

# ------------------------------------------------------------------- physics
V0 = 20.0
ANGLE_DEG = 30.0
G_ACC = 10.0
ANGLE_RAD = math.radians(ANGLE_DEG)

VX = V0 * math.cos(ANGLE_RAD)      # 17.3205... m/s
VY = V0 * math.sin(ANGLE_RAD)      # 10.0 m/s
T_APEX = VY / G_ACC                # 1.0 s
T_TOTAL = 2 * VY / G_ACC           # 2.0 s
H_MAX = VY ** 2 / (2 * G_ACC)      # 5.0 m
RANGE_M = VX * T_TOTAL             # 34.641... m

# --------------------------------------------------------------------- stage
POS_SCALE = 0.22        # scene units per metre, for ball positions
VEC_SCALE = 0.12        # scene units per (m/s), for the launch decomposition
LIVE_VEC_SCALE = 0.05   # scene units per (m/s), for the live indicators

RANGE_U = RANGE_M * POS_SCALE
LAUNCH_X = -RANGE_U / 2
GROUND_Y = -1.6
SHADOW_Y = GROUND_Y - 0.4
VERT_X = LAUNCH_X - 0.9
GROUND_X_MIN = VERT_X - 0.6
GROUND_X_MAX = LAUNCH_X + RANGE_U + 1.0

MAX_CAPTION_W = 11.5


def real_pt(t: float) -> list:
    x = LAUNCH_X + VX * t * POS_SCALE
    y = GROUND_Y + (VY * t - 0.5 * G_ACC * t * t) * POS_SCALE
    return [x, y, 0]


def shadow_pt(t: float) -> list:
    return [LAUNCH_X + VX * t * POS_SCALE, SHADOW_Y, 0]


def vert_pt(t: float) -> list:
    y = GROUND_Y + (VY * t - 0.5 * G_ACC * t * t) * POS_SCALE
    return [VERT_X, y, 0]


def live_vx_arrow(t: float) -> Arrow:
    """Constant-length arrow riding the real ball: horizontal speed never changes."""
    p = real_pt(t)
    y = p[1] + 0.32
    return Arrow([p[0], y, 0], [p[0] + VX * LIVE_VEC_SCALE, y, 0],
                 buff=0, color=BLUE_C, stroke_width=5)


def live_vy_arrow(t: float) -> Arrow:
    """Arrow riding the real ball: shrinks to a stub at the apex, then flips."""
    p = real_pt(t)
    vy_t = VY - G_ACC * t
    length = max(abs(vy_t), 0.4) * LIVE_VEC_SCALE
    direction = 1 if vy_t >= 0 else -1
    x = p[0] + 0.32
    return Arrow([x, p[1], 0], [x, p[1] + direction * length, 0],
                 buff=0, color=ORANGE, stroke_width=5)


# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_ground", "reveal_ground", ()),
    ("intro_velocity", "show_velocity", ()),
    ("intro_angle", "show_angle", ()),
    ("intro_rule", "show_rule", ()),
    ("intro_rule2", "pulse_rule", ()),

    ("decomp_vx", "decompose_vx", ()),
    ("decomp_vy", "decompose_vy", ()),
    ("clear_setup", "clear_setup", ()),

    ("intro_balls", "spawn_balls", ()),
    ("label_balls", "label_balls", ()),

    ("p1_rise1", "fly", (0.0, 0.35)),
    ("p1_rise2", "fly", (0.35, 0.70)),
    ("p1_rise3", "fly", (0.70, 1.00)),

    ("apex_hit", "apex_flash", ()),
    ("apex_numbers", "show_apex_numbers", ()),

    ("p2_fall1", "fly", (1.00, 1.35)),
    ("p2_fall2", "fly", (1.35, 1.70)),
    ("p2_fall3", "fly", (1.70, 2.00)),

    ("land_time", "show_time_total", ()),
    ("land_range", "show_range", ()),

    ("recap_shadow", "emphasize_shadow", ()),
    ("recap_vertical", "emphasize_vertical", ()),
    ("recap_claim", "emphasize_rule", ()),

    ("an_formula_t", "show_formula_time", ()),
    ("an_formula_r", "show_formula_range", ()),

    ("end_sweep", "final_sweep", ()),
    ("end_line", "fade_out", ()),
]

ACTION_P = 0.40


class ProjectileMotion(TimedScene):
    TOPIC = "projectile_motion"
    STATUS_AT = DOWN * 3.3

    def construct(self):
        self.setup_timing()
        self.v0_arrow = self.v0_label = None
        self.angle_arc = self.angle_label = None
        self.vx_arrow = self.vx_label = None
        self.vy_arrow = self.vy_label = None
        self.rule_badge = None
        self.legend = None
        self.ground = self.shadow_track = self.vert_track = None
        self.real_ball = self.shadow_ball = self.vert_ball = None
        self.vx_live = self.vy_live = None
        self.trace = VGroup()
        self.results: list[Mobject] = []
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
        self.title = Text("Projectile Motion", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

    def _result_line(self, tex: str) -> MathTex:
        """Grow a small persistent results column in the corner, one line per call."""
        line = MathTex(tex, color=YELLOW).scale(0.55)
        if not self.results:
            line.to_corner(UR, buff=0.5)
        else:
            line.next_to(self.results[-1], DOWN, buff=0.15, aligned_edge=RIGHT)
        self.results.append(line)
        return line

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_ground(self, c: BeatClock):
        self.ground = Line(
            [GROUND_X_MIN, GROUND_Y, 0], [GROUND_X_MAX, GROUND_Y, 0],
            stroke_width=4, color=GREY_B,
        )
        c.play(Create(self.ground), p=ACTION_P, cap=2.2)

    def show_velocity(self, c: BeatClock):
        start = [LAUNCH_X, GROUND_Y, 0]
        end = [LAUNCH_X + VX * VEC_SCALE, GROUND_Y + VY * VEC_SCALE, 0]
        self.v0_arrow = Arrow(start, end, buff=0, color=WHITE, stroke_width=5)
        self.v0_label = MathTex(r"v_0 = 20 \text{ m/s}").scale(0.5)
        # Offset perpendicular to the arrow (not just upward), so the label
        # never crosses the shaft or the arrowhead regardless of arrow slope.
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        perp = (-dy / length, dx / length)
        mid = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2, 0]
        self.v0_label.move_to([mid[0] + perp[0] * 0.4, mid[1] + perp[1] * 0.4, 0])
        c.play(GrowArrow(self.v0_arrow), Write(self.v0_label), p=ACTION_P, cap=2.4)

    def show_angle(self, c: BeatClock):
        ground_ray = Line([LAUNCH_X, GROUND_Y, 0], [LAUNCH_X + 1.4, GROUND_Y, 0])
        self.angle_arc = Angle(ground_ray, self.v0_arrow, radius=0.55, color=GOLD)
        self.angle_label = MathTex(r"30^\circ", color=GOLD).scale(0.5)
        self.angle_label.move_to(
            Angle(ground_ray, self.v0_arrow, radius=0.9).point_from_proportion(0.5)
        )
        c.play(Create(self.angle_arc), Write(self.angle_label), p=ACTION_P, cap=2.0)

    def show_rule(self, c: BeatClock):
        self.rule_badge = MathTex(
            r"\text{horizontal and vertical: independent}", color=GREY_A
        ).scale(0.5).to_corner(UL, buff=0.5)
        c.play(FadeIn(self.rule_badge, shift=RIGHT * 0.2), p=ACTION_P, cap=1.8)

    def pulse_rule(self, c: BeatClock):
        c.play(Indicate(self.rule_badge, scale_factor=1.08, color=GOLD), p=ACTION_P, cap=1.8)

    def decompose_vx(self, c: BeatClock):
        start = [LAUNCH_X, GROUND_Y, 0]
        end = [LAUNCH_X + VX * VEC_SCALE, GROUND_Y, 0]
        self.vx_arrow = Arrow(start, end, buff=0, color=BLUE_C, stroke_width=4)
        self.vx_label = MathTex(r"v_x = 17.3 \text{ m/s}", color=BLUE_C).scale(0.46)
        # Below the arrow: v0/vy both rise up-right from here, so DOWN is the
        # only side that never crosses them. Safe from the ground/shadow track
        # too, since clear_setup fades this whole group before spawn_balls.
        self.vx_label.next_to(self.vx_arrow, DOWN, buff=0.15)
        c.play(GrowArrow(self.vx_arrow), Write(self.vx_label), p=ACTION_P, cap=2.2)

    def decompose_vy(self, c: BeatClock):
        start = [LAUNCH_X + VX * VEC_SCALE, GROUND_Y, 0]
        end = [LAUNCH_X + VX * VEC_SCALE, GROUND_Y + VY * VEC_SCALE, 0]
        self.vy_arrow = Arrow(start, end, buff=0, color=ORANGE, stroke_width=4)
        self.vy_label = MathTex(r"v_y = 10 \text{ m/s}", color=ORANGE).scale(0.46)
        self.vy_label.next_to(self.vy_arrow, RIGHT, buff=0.15)
        c.play(GrowArrow(self.vy_arrow), Write(self.vy_label), p=ACTION_P, cap=2.2)

    def spawn_balls(self, c: BeatClock):
        self.shadow_track = DashedLine(
            [LAUNCH_X, SHADOW_Y, 0], [LAUNCH_X + RANGE_U + 0.3, SHADOW_Y, 0],
            color=BLUE_C, stroke_width=2, dash_length=0.12,
        )
        self.vert_track = DashedLine(
            [VERT_X, GROUND_Y, 0], [VERT_X, GROUND_Y + H_MAX * POS_SCALE + 0.2, 0],
            color=TEAL, stroke_width=2, dash_length=0.1,
        )
        self.real_ball = Dot(radius=0.14, color=YELLOW).move_to(real_pt(0.0))
        self.shadow_ball = Dot(radius=0.11, color=BLUE_C).move_to(shadow_pt(0.0))
        self.vert_ball = Dot(radius=0.11, color=TEAL).move_to(vert_pt(0.0))
        c.play(
            Create(self.shadow_track), Create(self.vert_track),
            GrowFromCenter(self.real_ball),
            GrowFromCenter(self.shadow_ball),
            GrowFromCenter(self.vert_ball),
            p=ACTION_P, cap=2.4,
        )

    def label_balls(self, c: BeatClock):
        lines = [
            MathTex(r"\text{real: full flight}", color=YELLOW).scale(0.4),
            MathTex(r"\text{ground shadow: sideways only}", color=BLUE_C).scale(0.4),
            MathTex(r"\text{height shadow: straight up only}", color=TEAL).scale(0.4),
        ]
        lines[0].next_to(self.rule_badge, DOWN, buff=0.25, aligned_edge=LEFT)
        lines[1].next_to(lines[0], DOWN, buff=0.12, aligned_edge=LEFT)
        lines[2].next_to(lines[1], DOWN, buff=0.12, aligned_edge=LEFT)
        self.legend = VGroup(*lines)
        c.play(LaggedStart(*(Write(l) for l in lines), lag_ratio=0.3), p=ACTION_P, cap=2.6)

    def clear_setup(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(
                self.v0_arrow, self.v0_label, self.angle_arc, self.angle_label,
                self.vx_arrow, self.vx_label, self.vy_arrow, self.vy_label,
            )),
            p=ACTION_P, cap=2.0,
        )

    def fly(self, c: BeatClock, t0: float, t1: float):
        """Advance all three balls (and the live vectors) from t0 to t1."""
        curve = ParametricFunction(
            real_pt, t_range=[t0, t1, (t1 - t0) / 40], color=YELLOW_E, stroke_width=3,
        )
        new_vx, new_vy = live_vx_arrow(t1), live_vy_arrow(t1)
        anims = [
            Create(curve),
            MoveAlongPath(self.real_ball, curve),
            self.shadow_ball.animate.move_to(shadow_pt(t1)),
            self.vert_ball.animate.move_to(vert_pt(t1)),
        ]
        if self.vx_live is None:
            self.vx_live, self.vy_live = new_vx, new_vy
            anims += [FadeIn(self.vx_live), FadeIn(self.vy_live)]
        else:
            anims += [Transform(self.vx_live, new_vx), Transform(self.vy_live, new_vy)]
        c.play(*anims, p=ACTION_P, cap=2.6)
        self.trace.add(curve)

    def apex_flash(self, c: BeatClock):
        c.play(
            Flash(self.real_ball.get_center(), color=RED, line_length=0.18, num_lines=10),
            p=ACTION_P, cap=1.8,
        )

    def show_apex_numbers(self, c: BeatClock):
        line1 = self._result_line(r"t_{\text{apex}} = 1 \text{ s}")
        line2 = self._result_line(r"h_{\max} = 5 \text{ m}")
        c.play(
            FadeIn(line1, shift=RIGHT * 0.2), FadeIn(line2, shift=RIGHT * 0.2),
            p=ACTION_P, cap=1.8,
        )

    def show_time_total(self, c: BeatClock):
        line = self._result_line(r"t_{\text{total}} = 2 \text{ s}")
        c.play(FadeIn(line, shift=RIGHT * 0.2), p=ACTION_P, cap=1.6)

    def show_range(self, c: BeatClock):
        line = self._result_line(r"R = 34.6 \text{ m}")
        c.play(FadeIn(line, shift=RIGHT * 0.2), p=ACTION_P, cap=1.6)

    def emphasize_shadow(self, c: BeatClock):
        c.play(Circumscribe(self.shadow_track, color=BLUE_C, buff=0.1), p=ACTION_P, cap=2.0)

    def emphasize_vertical(self, c: BeatClock):
        c.play(Circumscribe(self.vert_track, color=TEAL, buff=0.1), p=ACTION_P, cap=2.0)

    def emphasize_rule(self, c: BeatClock):
        c.play(Circumscribe(self.rule_badge, color=GOLD, buff=0.15), p=ACTION_P, cap=2.0)

    def show_formula_time(self, c: BeatClock):
        self.formula = MathTex(r"T = \frac{2 v_y}{g}").scale(0.85).move_to([0, 2.3, 0])
        c.play(Write(self.formula), p=ACTION_P, cap=2.0)

    def show_formula_range(self, c: BeatClock):
        new = MathTex(r"R = v_x \times T").scale(0.85).move_to([0, 2.3, 0])
        c.play(FadeTransform(self.formula, new), p=ACTION_P, cap=1.8)
        self.formula = new

    def final_sweep(self, c: BeatClock):
        c.play(
            Indicate(
                VGroup(self.real_ball, self.shadow_ball, self.vert_ball),
                scale_factor=1.25, color=GOLD,
            ),
            p=ACTION_P + 0.05, cap=2.2,
        )

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(
                self.title, self.rule_badge, self.legend,
                self.ground, self.shadow_track, self.vert_track,
                self.real_ball, self.shadow_ball, self.vert_ball,
                self.vx_live, self.vy_live,
                self.trace, VGroup(*self.results), self.formula,
            )),
            p=ACTION_P, cap=2.4,
        )
