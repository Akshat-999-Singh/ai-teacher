"""Newton's method on f(x) = x^2 - 2 from x0 = 2, one hop or one digit per sentence.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/newtons_method.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption first.
The brief, with its trace and rejected inputs, is scripts/newtons_method.brief.md.

Deliberately not `derivative` or `derivatives`: the tangent here is a ruler used
once per step. A yellow dot climbs a dashed riser to the curve, then rides the
tangent down to the axis, where the next guess is ticked. Steps are discrete
hops, so there is no ValueTracker.

Step 2 is 0.17 units wide on the main plot and step 3 would be 0.05 wide even
at x10, so each opens a zoom inset in the right panel, grown out of a teal box
drawn on the previous view (x10, then x250). The insets do not keep equal aspect;
each window is sized so its step runs about 1.2-1.7 units and rises 1.4-1.7.
Step 4 is 2e-6 wide, which is where the video switches to a digit table. Digits
are truncated, not rounded, so the green prefixes (1, 3, 6, 12 correct digits)
can never be flattered by a carry.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

getcontext().prec = 50

X0 = Fraction(2)
STEPS = 4
DECIMALS = 12


def f(x):
    return x * x - 2


def df(x):
    return 2 * x


def newton_iterates() -> list[Fraction]:
    xs = [X0]
    for _ in range(STEPS):
        x = xs[-1]
        xs.append(x - f(x) / df(x))
    return xs


XS = newton_iterates()                 # 2, 3/2, 17/12, 577/408, 665857/470832
ROOT = Decimal(2).sqrt()


def digits(value: Decimal | Fraction) -> str:
    """Truncated to DECIMALS places: a rounding carry must never fake a correct digit."""
    if isinstance(value, Fraction):
        value = Decimal(value.numerator) / Decimal(value.denominator)
    whole, _, frac = format(value, "f").partition(".")  # Decimal 2 formats as "2", no point
    return f"{whole}.{(frac + '0' * DECIMALS)[:DECIMALS]}"


def correct_prefix_len(s: str, truth: str) -> tuple[int, int]:
    """(correct significant digits, characters they span including the point)."""
    count = chars = 0
    for a, b in zip(s, truth):
        if a != b:
            break
        chars += 1
        if a.isdigit():
            count += 1
    while chars and not s[chars - 1].isdigit():  # never end a prefix on the point
        chars -= 1
    return count, chars


# name: (x window, y window, x_length, y_length, centre, tangent y floor, tag)
VIEWS = {
    "main": ((-0.5, 2.5), (-2.5, 3.5), 6.0, 4.2, (-3.3, 0.55, 0), -1.0, None),
    # y floor -0.1, not lower: on the main plot this box's bottom edge would cut the x1 label.
    "zoom1": ((1.34, 1.59), (-0.1, 0.45), 5.0, 3.6, (3.9, 0.55, 0), None, r"\times 10"),
    "zoom2": ((1.4125, 1.4225), (-0.006, 0.012), 5.0, 3.6, (3.9, 0.55, 0), None, r"\times 250"),
}

FORMULA_POS = (3.9, 2.2, 0)
LABEL_X, DIGITS_LEFT, ERROR_X = 1.2, 1.75, 6.0
HEADER_Y = 1.2
ROW_Y = (0.75, 0.3, -0.15, -0.6, -1.05)

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

CURVE_COLOR = BLUE
GUESS_COLOR = YELLOW
TANGENT_COLOR = ORANGE
ROOT_COLOR = GREEN
ZOOM_COLOR = TEAL
FAIL_COLOR = RED

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_curve", "draw_curve", ()),
    ("intro_root", "ring_root", ()),
    ("intro_sqrt2", "label_root", ()),
    ("intro_guess", "place_guess", ()),

    ("s1_rise", "rise", ("main", 0)),
    ("s1_tangent", "tangent", ("main", 0)),
    ("s1_slide", "slide", ("main", 0)),

    ("z1_box", "zoom_box", ("main", "zoom1")),
    ("z1_open", "open_inset", ("main", "zoom1", 1)),
    ("s2_rise", "rise", ("zoom1", 1)),
    ("s2_tangent", "tangent", ("zoom1", 1)),
    ("s2_slide", "slide", ("zoom1", 1)),

    ("z2_box", "zoom_box", ("zoom1", "zoom2")),
    ("z2_open", "open_inset", ("zoom1", "zoom2", 2)),
    ("s3_rise", "rise", ("zoom2", 2)),
    ("s3_tangent", "tangent", ("zoom2", 2)),
    ("s3_slide", "slide", ("zoom2", 2)),

    ("rule_step", "show_rule", ()),
    ("rule_sqrt2", "set_formula", (r"x_{n+1} = \frac{1}{2}\left(x_n + \frac{2}{x_n}\right)",)),

    ("d_table", "show_table", (4,)),
    ("d_x1", "mark_digits", (1, 1)),
    ("d_x2", "mark_digits", (2, 3)),
    ("d_x3", "mark_digits", (3, 6)),
    ("d_x4", "add_row", (4, 12)),
    ("d_why", "show_errors", ()),

    ("warn_flat", "flat_tangent", ()),
    ("warn_never", "never_meets", ()),

    ("end_digits", "sweep_digits", ()),
    ("end_line", "fade_out", ()),
]


class View:
    """One plot window: its axes and what has been drawn in it. Not a Mobject."""

    def __init__(self, name: str):
        (self.xr, self.yr, self.xl, self.yl, self.center, self.floor, self.tag) = VIEWS[name]
        self.name = name
        self.dot = None
        self.tangent = None
        self.box = None       # zoom box drawn in this view, for the next view
        self.group = VGroup()  # everything to fade when the view is retired


class NewtonsMethod(TimedScene):
    TOPIC = "newtons_method"
    STATUS_AT = DOWN * 2.35

    def construct(self):
        self.setup_timing()
        self.formula = None
        self.rows: dict[int, VGroup] = {}
        self.prefixes: dict[int, VGroup] = {}
        self.errors = None
        self.fail_dot = self.fail_line = self.fail_label = None

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
        self.title = Text("Newton's Method", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

        self.views = {name: self.build_view(name) for name in VIEWS}
        main = self.views["main"]
        self.curve_label = MathTex(r"f(x) = x^2 - 2", color=CURVE_COLOR).scale(0.7)
        self.curve_label.move_to(main.axes.c2p(0.6, 3.0))

        self.table_head = VGroup(
            MathTex(r"\text{guess}", color=GREY_B).scale(0.55).move_to([LABEL_X, HEADER_Y, 0]),
            MathTex(r"\text{value}", color=GREY_B).scale(0.55).move_to([DIGITS_LEFT + 1.6, HEADER_Y, 0]),
            MathTex(r"\text{error}", color=GREY_B).scale(0.55).move_to([ERROR_X, HEADER_Y, 0]),
            Line([LABEL_X - 0.4, HEADER_Y - 0.25, 0], [ERROR_X + 0.8, HEADER_Y - 0.25, 0], color=GREY_D, stroke_width=2),
        )

    def build_view(self, name: str) -> View:
        view = View(name)
        inset = view.tag is not None
        axes = Axes(
            x_range=[*view.xr, 0.5],
            y_range=[*view.yr, 1],
            x_length=view.xl,
            y_length=view.yl,
            tips=False,
            axis_config={"color": GREY_C, "stroke_width": 2, "include_ticks": not inset},
            # No -2: the flat tangent of the warning runs straight through it.
            y_axis_config={} if inset else {"numbers_to_include": [1, 2, 3], "font_size": 24},
        ).move_to(view.center)
        view.axes = axes

        lo = view.xr[0] if 2 + view.yr[0] <= 0 else max(view.xr[0], float(np.sqrt(2 + view.yr[0])))
        hi = min(view.xr[1], float(np.sqrt(2 + view.yr[1])))
        view.curve = axes.plot(lambda x: x * x - 2, x_range=[lo, hi], color=CURVE_COLOR, stroke_width=5)
        view.ring = Circle(radius=0.09, color=ROOT_COLOR, stroke_width=3).move_to(axes.c2p(float(ROOT), 0))
        # buff 0.2 keeps the label outside the zoom box drawn around the root.
        view.root_label = MathTex(r"\sqrt{2}", color=ROOT_COLOR).scale(0.55).next_to(view.ring, UL, buff=0.2)
        view.group.add(axes, view.curve, view.ring, view.root_label)

        if inset:
            view.frame = Rectangle(width=view.xl + 0.3, height=view.yl + 0.3, color=ZOOM_COLOR, stroke_width=3)
            view.frame.move_to(view.center)
            tag = MathTex(view.tag, color=ZOOM_COLOR).scale(0.55)
            view.tag_mob = tag.next_to(view.frame.get_corner(UL), DR, buff=0.12)
            view.group.add(view.frame, view.tag_mob)
        return view

    def pt(self, view: View, x, y) -> np.ndarray:
        return view.axes.c2p(float(x), float(y))

    def tick(self, view: View, n: int) -> VGroup:
        at = self.pt(view, XS[n], 0)
        mark = Line(at + DOWN * 0.08, at + UP * 0.08, color=GUESS_COLOR, stroke_width=3)
        label = MathTex(f"x_{{{n}}}", color=GUESS_COLOR).scale(0.55).next_to(mark, DOWN, buff=0.1)
        group = VGroup(mark, label)
        view.group.add(group)
        return group

    def clipped_tangent(self, view: View, x) -> Line:
        """Tangent at x (slope 2x > 0 here), clipped to the view and its floor."""
        x, m = float(x), float(df(x))
        y0 = float(f(x))
        y_lo = view.yr[0] if view.floor is None else view.floor
        x_lo = max(view.xr[0], x + (y_lo - y0) / m)
        x_hi = min(view.xr[1], x + (view.yr[1] - y0) / m)
        # Under the curve and wider than it: where the two coincide (all of the x250
        # inset) the tangent shows as an orange edge instead of hiding the curve.
        return Line(
            self.pt(view, x_lo, y0 + m * (x_lo - x)),
            self.pt(view, x_hi, y0 + m * (x_hi - x)),
            color=TANGENT_COLOR, stroke_width=9,
        ).set_z_index(-1)

    def digit_row(self, n: int) -> VGroup:
        """x_n to DECIMALS places, one submobject per character so a prefix can turn green."""
        s = digits(XS[n])
        _, chars = correct_prefix_len(s, digits(ROOT))
        value = MathTex(*s).scale(0.6)
        value.move_to([DIGITS_LEFT, ROW_Y[n], 0], aligned_edge=LEFT)
        label = MathTex(f"x_{{{n}}}", color=GUESS_COLOR).scale(0.6).move_to([LABEL_X, ROW_Y[n], 0])
        self.rows[n] = VGroup(label, value)
        self.prefixes[n] = VGroup(*value[:chars])
        return self.rows[n]

    def check_digits(self, n: int, count: int):
        """The narration states each count; fail the dry run if the arithmetic disagrees."""
        got, _ = correct_prefix_len(digits(XS[n]), digits(ROOT))
        if got != count:
            raise AssertionError(f"x{n} has {got} correct digits, SCRIPT says {count}")

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def draw_curve(self, c: BeatClock):
        main = self.views["main"]
        c.play(
            LaggedStart(Create(main.axes), Create(main.curve), FadeIn(self.curve_label), lag_ratio=0.35),
            p=ACTION_P,
            cap=2.4,
        )

    def ring_root(self, c: BeatClock):
        ring = self.views["main"].ring
        c.play(GrowFromCenter(ring), Flash(ring, color=ROOT_COLOR, flash_radius=0.25), p=ACTION_P, cap=1.4)

    def label_root(self, c: BeatClock):
        c.play(FadeIn(self.views["main"].root_label, shift=DOWN * 0.15), p=ACTION_P, cap=1.4)

    def place_guess(self, c: BeatClock):
        main = self.views["main"]
        main.dot = Dot(self.pt(main, XS[0], 0), radius=0.08, color=GUESS_COLOR)
        main.group.add(main.dot)
        c.play(FadeIn(self.tick(main, 0), shift=UP * 0.15), GrowFromCenter(main.dot), p=ACTION_P, cap=1.4)

    def rise(self, c: BeatClock, name: str, n: int):
        view = self.views[name]
        top = self.pt(view, XS[n], f(XS[n]))
        riser = DashedLine(self.pt(view, XS[n], 0), top, color=GREY_B, stroke_width=3)
        view.group.add(riser)
        c.play(Create(riser), view.dot.animate.move_to(top), p=ACTION_P, cap=1.4)

    def tangent(self, c: BeatClock, name: str, n: int):
        view = self.views[name]
        view.tangent = self.clipped_tangent(view, XS[n])
        view.group.add(view.tangent)
        c.play(Create(view.tangent), p=ACTION_P, cap=1.6)

    def slide(self, c: BeatClock, name: str, n: int):
        """Ride the tangent from (x_n, f(x_n)) down to (x_{n+1}, 0)."""
        view = self.views[name]
        path = Line(self.pt(view, XS[n], f(XS[n])), self.pt(view, XS[n + 1], 0))
        c.play(
            MoveAlongPath(view.dot, path),
            FadeIn(self.tick(view, n + 1), shift=UP * 0.15),
            p=ACTION_P,
            cap=1.8,
        )

    def zoom_box(self, c: BeatClock, outer: str, inner: str):
        """Outline, in the outer view, exactly the window the inner view will show."""
        view, target = self.views[outer], self.views[inner]
        (x0, x1), (y0, y1) = target.xr, target.yr
        a, b = self.pt(view, x0, y0), self.pt(view, x1, y1)
        view.box = Rectangle(width=b[0] - a[0], height=b[1] - a[1], color=ZOOM_COLOR, stroke_width=3)
        view.box.move_to((a + b) / 2)
        view.group.add(view.box)
        anims = [Create(view.box)]
        # The x250 window is a few pixels wide inside the x10 inset; a ring that stays
        # finds it. The x10 box on the main plot is plainly visible and gets none.
        if view.box.width < 0.3:
            finder = Circle(radius=0.3, color=ZOOM_COLOR, stroke_width=2).move_to(view.box)
            view.group.add(finder)
            anims.append(Create(finder))
        c.play(*anims, p=ACTION_P, cap=1.4)

    def open_inset(self, c: BeatClock, outer: str, inner: str, n: int):
        """Grow the inner view out of the box; retire the previous inset if there was one."""
        view, target = self.views[outer], self.views[inner]
        target.dot = Dot(self.pt(target, XS[n], 0), radius=0.08, color=GUESS_COLOR)
        target.group.add(target.dot)
        contents = VGroup(target.axes, target.curve, target.ring, target.root_label, target.tag_mob, self.tick(target, n), target.dot)
        retire = [FadeOut(view.group)] if view.tag is not None else []
        c.play(
            TransformFromCopy(view.box, target.frame),
            FadeIn(contents),
            *retire,
            p=ACTION_P,
            cap=1.8,
        )

    def show_rule(self, c: BeatClock):
        self.formula = MathTex(r"x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}").scale(0.75).move_to(FORMULA_POS)
        c.play(FadeOut(self.views["zoom2"].group), Write(self.formula), p=ACTION_P, cap=1.8)

    def set_formula(self, c: BeatClock, tex: str):
        nxt = MathTex(tex).scale(0.75).move_to(FORMULA_POS)
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.6)
        self.formula = nxt

    def show_table(self, c: BeatClock, rows: int):
        c.play(
            FadeIn(self.table_head),
            LaggedStart(*(FadeIn(self.digit_row(n), shift=RIGHT * 0.2) for n in range(rows)), lag_ratio=0.3),
            p=ACTION_P,
            cap=2.2,
        )

    def mark_digits(self, c: BeatClock, n: int, count: int):
        self.check_digits(n, count)
        prefix = self.prefixes[n]
        c.play(
            prefix.animate.set_color(ROOT_COLOR),
            Circumscribe(prefix, color=ROOT_COLOR, buff=0.06),
            p=ACTION_P,
            cap=1.6,
        )

    def add_row(self, c: BeatClock, n: int, count: int):
        self.check_digits(n, count)
        row = self.digit_row(n)
        self.prefixes[n].set_color(ROOT_COLOR)
        c.play(FadeIn(row, shift=RIGHT * 0.2), Circumscribe(self.prefixes[n], color=ROOT_COLOR, buff=0.06), p=ACTION_P, cap=1.8)

    def show_errors(self, c: BeatClock):
        cells = []
        for n in range(len(XS)):
            err = abs(Decimal(XS[n].numerator) / Decimal(XS[n].denominator) - ROOT)
            exponent = round(float(err.log10()))
            cells.append(MathTex(rf"\approx 10^{{{exponent}}}", color=GREY_A).scale(0.55).move_to([ERROR_X, ROW_Y[n], 0]))
        self.errors = VGroup(*cells)
        c.play(LaggedStart(*(Write(cell) for cell in cells), lag_ratio=0.3), p=ACTION_P, cap=2.2)

    def flat_tangent(self, c: BeatClock):
        main = self.views["main"]
        at = self.pt(main, 0, f(0))
        self.fail_dot = Dot(at, radius=0.08, color=FAIL_COLOR)
        self.fail_line = Line(self.pt(main, -0.4, -2), self.pt(main, 2.4, -2), color=FAIL_COLOR, stroke_width=4)
        self.fail_label = MathTex(r"x_0 = 0", color=FAIL_COLOR).scale(0.55).next_to(self.fail_dot, DR, buff=0.1)
        c.play(
            GrowFromCenter(self.fail_dot),
            Create(self.fail_line),
            FadeIn(self.fail_label),
            p=ACTION_P,
            cap=1.6,
        )

    def never_meets(self, c: BeatClock):
        main = self.views["main"]
        c.play(
            MoveAlongPath(self.fail_dot, Line(self.pt(main, 0, -2), self.pt(main, 2.4, -2))),
            rate_func=linear,
            p=ACTION_P + 0.1,
            cap=2.4,
        )

    def sweep_digits(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(self.prefixes[n], scale_factor=1.15, color=ROOT_COLOR) for n in range(1, len(XS))),
                lag_ratio=0.35,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def fade_out(self, c: BeatClock):
        main = self.views["main"]
        c.play(
            FadeOut(VGroup(main.group, self.curve_label, self.fail_dot, self.fail_line, self.fail_label)),
            FadeOut(VGroup(self.title, self.formula, self.table_head, self.errors, *self.rows.values())),
            p=ACTION_P,
            cap=2.0,
        )
