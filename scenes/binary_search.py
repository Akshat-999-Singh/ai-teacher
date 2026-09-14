"""Binary search for 7 in [1, 3, 4, 7, 9, 12, 15, 18], one sentence at a time.

Same contract as bubble_sort: every entry in SCRIPT pairs a beat name from
scripts/binary_search.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption before the
action runs. See scenes/beat_timing.py.

Bounds are half-open, [lo, hi): `hi` marks one *past* the live window. That is
the convention in bisect / sort.Search, and on this input it is the one that
teaches -- with inclusive bounds, (0 + 7) // 2 is 3 and a[3] is already 7, so
the search would end on its first probe with nothing halved. Half-open probes
index 4, then 2, then 3, shrinking the window 8 -> 4 -> 1: exactly log2(8).

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

VALUES = [1, 3, 4, 7, 9, 12, 15, 18]
TARGET = 7

CELL_SIZE = 0.95
CELL_GAP = 1.25
ARRAY_Y = 1.25
INDEX_Y = 0.42
BOUND_Y = -0.5
MID_Y = -1.25
MAX_CAPTION_W = 11.5

WINDOW_COLOR = BLUE_B
LO_COLOR = TEAL_B
HI_COLOR = PURPLE_B
MID_COLOR = YELLOW
FOUND_COLOR = GREEN
DIM_OPACITY = 0.2

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_array", "reveal_array", ()),
    ("intro_sorted", "sweep_sorted", ()),
    ("intro_target", "show_target", ()),
    ("setup_window", "show_window", ()),
    ("setup_bounds", "show_bounds", ()),
    ("rule_count", "show_counter", ()),

    ("p1_mid", "probe", (4,)),
    ("p1_compare", "examine", (4,)),
    ("p1_verdict", "discard", (4, 8)),
    ("p1_shrink", "move_hi", (4,)),
    ("p1_left", "note_window", ()),

    ("p2_mid", "probe", (2,)),
    ("p2_compare", "examine", (2,)),
    ("p2_verdict", "discard", (0, 3)),
    ("p2_shrink", "move_lo", (3,)),
    ("p2_left", "note_window", ()),

    ("p3_mid", "probe", (3,)),
    ("p3_compare", "examine", (3,)),
    ("p3_found", "found", (3,)),
    ("p3_index", "show_index", (3,)),

    ("an_windows", "show_trail", ()),
    ("an_half", "emphasize_half", ()),
    ("an_log", "show_pow2", ()),
    ("an_double", "show_double", ()),
    ("an_formula", "show_log", ()),

    ("end_linear", "linear_contrast", ()),
    ("end_sorted", "highlight_sorted", ()),
    ("end_line", "fade_out", ()),
]

ACTION_P = 0.40


class BinarySearch(TimedScene):
    TOPIC = "binary_search"
    STATUS_AT = DOWN * 2.35

    def construct(self):
        self.setup_timing()
        self.lo, self.hi = 0, len(VALUES)
        self.comparisons = 0
        self.dimmed: set[int] = set()
        self.window = None
        self.lo_ptr = self.hi_ptr = self.mid_ptr = None
        self.counter = None
        self.target_badge = None
        self.trail = None
        self.formula = None
        self.found_label = None

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
        """x of index i. Defined past the last cell so half-open hi has a home."""
        return (i - (len(VALUES) - 1) / 2) * CELL_GAP

    def build_stage(self):
        self.title = Text("Binary Search", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

        self.cells = []
        self.index_labels = VGroup()
        for i, value in enumerate(VALUES):
            square = Square(side_length=CELL_SIZE, stroke_width=4, color=BLUE_D)
            square.set_fill(BLUE_E, opacity=0.3)
            label = MathTex(str(value)).scale(0.85)
            cell = VGroup(square, label).move_to([self.slot_x(i), ARRAY_Y, 0])
            self.cells.append(cell)
            self.index_labels.add(
                MathTex(str(i), color=GREY_C).scale(0.5).move_to([self.slot_x(i), INDEX_Y, 0])
            )
        self.array = VGroup(*self.cells)

    def live_cells(self) -> VGroup:
        return VGroup(*self.cells[self.lo:self.hi])

    def window_rect(self) -> VMobject:
        return SurroundingRectangle(
            self.live_cells(), color=WINDOW_COLOR, buff=0.18, corner_radius=0.12,
            stroke_width=4,
        )

    def pointer(self, name: str, colour, index: int, y: float) -> VGroup:
        tip = Triangle(color=colour, fill_opacity=1, stroke_width=0).scale(0.13)
        label = Text(name, weight=BOLD).scale(0.42).set_color(colour)
        group = VGroup(tip, label).arrange(DOWN, buff=0.1)
        return group.move_to([self.slot_x(index), y, 0])

    def counter_text(self, n: int) -> Text:
        text = Text(f"comparisons: {n}", weight=BOLD).scale(0.5)
        text.set_color(MID_COLOR if n else GREY_B).to_corner(UR, buff=0.5)
        return text

    def counter_tick(self) -> Animation:
        """Counter bump, folded into whatever play is already running."""
        self.comparisons += 1
        new = self.counter_text(self.comparisons)
        anim = FadeTransform(self.counter, new)
        self.counter = new
        return anim

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_array(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(GrowFromCenter(cell) for cell in self.cells),
                *(FadeIn(lbl) for lbl in self.index_labels),
                lag_ratio=0.12,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def sweep_sorted(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.12, color=WINDOW_COLOR) for cell in self.cells),
                lag_ratio=0.18,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def show_target(self, c: BeatClock):
        self.target_badge = MathTex(
            r"\text{target} = " + str(TARGET), color=MID_COLOR
        ).scale(0.8).to_corner(UL, buff=0.5)
        c.play(FadeIn(self.target_badge, shift=RIGHT * 0.2), p=ACTION_P, cap=1.4)

    def show_window(self, c: BeatClock):
        self.window = self.window_rect()
        c.play(Create(self.window), p=ACTION_P, cap=1.8)

    def show_bounds(self, c: BeatClock):
        self.lo_ptr = self.pointer("lo", LO_COLOR, self.lo, BOUND_Y)
        self.hi_ptr = self.pointer("hi", HI_COLOR, self.hi, BOUND_Y)
        c.play(
            FadeIn(self.lo_ptr, shift=UP * 0.25),
            FadeIn(self.hi_ptr, shift=UP * 0.25),
            p=ACTION_P,
            cap=1.6,
        )

    def show_counter(self, c: BeatClock):
        self.counter = self.counter_text(0)
        c.play(FadeIn(self.counter, shift=DOWN * 0.2), p=ACTION_P, cap=1.4)

    def probe(self, c: BeatClock, index: int):
        """Point mid at the middle of the live window."""
        target = self.pointer("mid", MID_COLOR, index, MID_Y)
        if self.mid_ptr is None:
            self.mid_ptr = target
            c.play(FadeIn(target, shift=UP * 0.25), p=ACTION_P, cap=1.4)
        else:
            c.play(Transform(self.mid_ptr, target), p=ACTION_P, cap=1.4)

    def examine(self, c: BeatClock, index: int):
        """Read the cell under mid. This is the comparison the counter counts."""
        c.play(
            self.cells[index][0].animate.set_stroke(MID_COLOR, width=8),
            Indicate(self.cells[index], scale_factor=1.15, color=MID_COLOR),
            self.counter_tick(),
            p=ACTION_P,
            cap=1.6,
        )

    def discard(self, c: BeatClock, start: int, stop: int):
        """Dim a half instead of deleting it, so the halving stays on screen."""
        fresh = [i for i in range(start, stop) if i not in self.dimmed]
        self.dimmed.update(fresh)
        c.play(
            LaggedStart(
                *(self.cells[i].animate.set_opacity(DIM_OPACITY) for i in fresh),
                lag_ratio=0.12,
            ),
            p=ACTION_P,
            cap=1.8,
        )

    def _move_bound(self, c: BeatClock, ptr: VGroup, index: int):
        moved = self.pointer(
            ptr[1].text, ptr[1].get_color(), index, BOUND_Y
        )
        c.play(
            Transform(ptr, moved),
            Transform(self.window, self.window_rect()),
            p=ACTION_P,
            cap=1.6,
        )

    def move_hi(self, c: BeatClock, index: int):
        self.hi = index
        self._move_bound(c, self.hi_ptr, index)

    def move_lo(self, c: BeatClock, index: int):
        self.lo = index
        self._move_bound(c, self.lo_ptr, index)

    def note_window(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(
                    Indicate(cell, scale_factor=1.12, color=WINDOW_COLOR)
                    for cell in self.live_cells()
                ),
                lag_ratio=0.2,
            ),
            p=ACTION_P,
            cap=1.8,
        )

    def found(self, c: BeatClock, index: int):
        square = self.cells[index][0]
        c.play(
            square.animate.set_fill(FOUND_COLOR, opacity=0.45).set_stroke(FOUND_COLOR, width=7),
            Transform(self.window, self.window_rect().set_color(FOUND_COLOR)),
            Circumscribe(self.cells[index], color=FOUND_COLOR, buff=0.14),
            p=ACTION_P,
            cap=2.0,
        )

    def show_index(self, c: BeatClock, index: int):
        # Between the window rect (top ~1.9) and the title (bottom ~3.0).
        self.found_label = MathTex(
            r"\text{found at index } " + str(index), color=FOUND_COLOR
        ).scale(0.8).move_to([self.slot_x(index), ARRAY_Y + 1.05, 0])
        c.play(FadeIn(self.found_label, shift=DOWN * 0.2), p=ACTION_P, cap=1.6)

    def show_trail(self, c: BeatClock):
        """Retire the pointers and put the window sizes on screen instead."""
        self.trail = MathTex(
            r"8 \;\longrightarrow\; 4 \;\longrightarrow\; 1", color=WINDOW_COLOR
        ).scale(0.95).move_to([0, BOUND_Y - 0.1, 0])
        c.play(
            FadeOut(self.lo_ptr),
            FadeOut(self.hi_ptr),
            FadeOut(self.mid_ptr),
            FadeOut(self.found_label),
            Write(self.trail),
            p=ACTION_P,
            cap=1.8,
        )

    def emphasize_half(self, c: BeatClock):
        c.play(Indicate(self.trail, scale_factor=1.15, color=MID_COLOR), p=ACTION_P, cap=1.6)

    def show_pow2(self, c: BeatClock):
        self.formula = MathTex(r"2^3 = 8 \quad\Longrightarrow\quad 3 \text{ comparisons}")
        self.formula.scale(0.8).move_to([0, MID_Y - 0.1, 0])
        c.play(Write(self.formula), p=ACTION_P, cap=1.8)

    def show_double(self, c: BeatClock):
        nxt = MathTex(r"2^4 = 16 \quad\Longrightarrow\quad 4 \text{ comparisons}")
        nxt.scale(0.8).move_to([0, MID_Y - 0.1, 0])
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.8)
        self.formula = nxt

    def show_log(self, c: BeatClock):
        nxt = MathTex(r"\log_2 n", color=MID_COLOR).scale(1.3)
        nxt.move_to([0, MID_Y - 0.1, 0])
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.8)
        self.formula = nxt

    def linear_contrast(self, c: BeatClock):
        """One cell at a time, for contrast with the three probes we needed."""
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.1, color=GREY_A) for cell in self.cells),
                lag_ratio=0.5,
            ),
            p=ACTION_P + 0.12,
            cap=2.8,
        )

    def highlight_sorted(self, c: BeatClock):
        c.play(
            FadeOut(self.trail),
            FadeOut(self.formula),
            LaggedStart(
                *(cell.animate.set_opacity(1.0) for cell in self.cells),
                lag_ratio=0.12,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(self.array, self.index_labels, self.window)),
            FadeOut(VGroup(self.title, self.counter, self.target_badge)),
            p=ACTION_P,
            cap=2.0,
        )
