"""Insertion sort on [5, 2, 9, 1, 6], one comparison or shift per sentence.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/insertion_sort.json with the single visible action that sentence
describes, and `self.beat(name)` writes the sentence as the caption first.

The key is lifted above the row and the vacated slot becomes a dashed "hole".
Each comparison puts a relation sign between the key and the cell left of the
hole (red ">" means that cell shifts, green "<" means stop); each shift slides
that cell into the hole while the hole and the key step one slot left. Sorted
cells are green, so the growing prefix is visible without a brace. The trace is
4 passes, 7 comparisons, 5 shifts.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

VALUES = [5, 2, 9, 1, 6]

CELL_SIZE = 1.0
CELL_GAP = 1.5
ARRAY_Y = 0.45
KEY_Y = ARRAY_Y + 1.4
INDEX_Y = ARRAY_Y - 0.8
FORMULA_Y = -1.1
MAX_CAPTION_W = 11.5
ACTION_P = 0.40

UNSORTED = (BLUE_D, BLUE_E)
SORTED = (GREEN_C, GREEN_E)
KEY = (YELLOW, YELLOW_E)
SHIFT_COLOR = RED
STOP_COLOR = GREEN
HOLE_COLOR = GREY_B
COUNT_COLOR = YELLOW

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_array", "reveal_array", ()),
    ("intro_hand", "sweep_hand", ()),
    ("intro_sorted", "mark_first_sorted", ()),
    ("rule_count", "show_counters", ()),

    ("p1_lift", "lift", (1,)),
    ("p1_cmp", "compare", (0, True)),
    ("p1_shift", "shift", (0,)),
    ("p1_insert", "insert", (0,)),

    ("p2_lift", "lift", (2,)),
    ("p2_cmp", "compare", (1, False)),
    ("p2_insert", "insert", (2,)),

    ("p3_lift", "lift", (3,)),
    ("p3_cmp1", "compare", (2, True)),
    ("p3_shift1", "shift", (2,)),
    ("p3_cmp2", "compare", (1, True)),
    ("p3_shift2", "shift", (1,)),
    ("p3_cmp3", "compare", (0, True)),
    ("p3_shift3", "shift", (0,)),
    ("p3_insert", "insert", (0,)),

    ("p4_lift", "lift", (4,)),
    ("p4_cmp1", "compare", (3, True)),
    ("p4_shift", "shift", (3,)),
    ("p4_cmp2", "compare", (2, False)),
    ("p4_insert", "insert", (3,)),

    ("an_sorted", "sweep_sorted", ()),
    ("an_counts", "emphasize_counters", ()),
    ("an_worst", "show_worst", ()),
    ("an_square", "show_square", ()),
    ("an_best", "show_best", ()),
    ("end_line", "fade_out", ()),
]


class InsertionSort(TimedScene):
    TOPIC = "insertion_sort"
    STATUS_AT = DOWN * 2.2

    def construct(self):
        self.setup_timing()
        self.comparisons = 0
        self.shifts = 0
        self.key = None
        self.hole = None
        self.relation = None
        self.formula = None
        self.cmp_counter = self.shift_counter = None

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
        self.title = Text("Insertion Sort", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)

        self.cells = []
        self.index_labels = VGroup()
        for i, value in enumerate(VALUES):
            square = Square(side_length=CELL_SIZE, stroke_width=4)
            self.style(square, UNSORTED)
            label = MathTex(str(value)).scale(0.9)
            cell = VGroup(square, label).move_to([self.slot_x(i), ARRAY_Y, 0])
            self.cells.append(cell)
            self.index_labels.add(
                MathTex(str(i), color=GREY_C).scale(0.5).move_to([self.slot_x(i), INDEX_Y, 0])
            )
        # slots[i] is the cell sitting at index i, or None where the hole is.
        self.slots = list(self.cells)
        self.array = VGroup(*self.cells)

    @staticmethod
    def style(square: VMobject, colours) -> VMobject:
        stroke, fill = colours
        return square.set_stroke(stroke, width=4).set_fill(fill, opacity=0.35)

    def moved(self, cell: VGroup, x: float, y: float, colours=None) -> Animation:
        """One Transform for position + colour, so the square and label never fight."""
        target = cell.copy().move_to([x, y, 0])
        if colours is not None:
            self.style(target[0], colours)
        return Transform(cell, target)

    def counter_text(self, name: str, n: int, corner) -> Text:
        text = Text(f"{name}: {n}", weight=BOLD).scale(0.5)
        return text.set_color(COUNT_COLOR if n else GREY_B).to_corner(corner, buff=0.5)

    def tick_comparisons(self) -> Animation:
        self.comparisons += 1
        new = self.counter_text("comparisons", self.comparisons, UL)
        anim = FadeTransform(self.cmp_counter, new)
        self.cmp_counter = new
        return anim

    def tick_shifts(self) -> Animation:
        self.shifts += 1
        new = self.counter_text("shifts", self.shifts, UR)
        anim = FadeTransform(self.shift_counter, new)
        self.shift_counter = new
        return anim

    def clear_relation(self) -> list[Animation]:
        if self.relation is None:
            return []
        old, self.relation = self.relation, None
        return [FadeOut(old)]

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_array(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(GrowFromCenter(cell) for cell in self.cells),
                *(FadeIn(lbl) for lbl in self.index_labels),
                lag_ratio=0.15,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def sweep_hand(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.12, color=GREY_A) for cell in self.cells),
                lag_ratio=0.25,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def mark_first_sorted(self, c: BeatClock):
        cell = self.cells[0]
        c.play(
            self.moved(cell, self.slot_x(0), ARRAY_Y, SORTED),
            Circumscribe(cell, color=SORTED[0], buff=0.12),
            p=ACTION_P,
            cap=1.6,
        )

    def show_counters(self, c: BeatClock):
        self.cmp_counter = self.counter_text("comparisons", 0, UL)
        self.shift_counter = self.counter_text("shifts", 0, UR)
        c.play(
            FadeIn(self.cmp_counter, shift=DOWN * 0.2),
            FadeIn(self.shift_counter, shift=DOWN * 0.2),
            p=ACTION_P,
            cap=1.4,
        )

    def lift(self, c: BeatClock, index: int):
        """Raise the key above the row and leave a dashed hole where it was."""
        self.key = self.slots[index]
        self.slots[index] = None
        self.hole = DashedVMobject(
            Square(side_length=CELL_SIZE, color=HOLE_COLOR, stroke_width=3), num_dashes=20
        ).move_to([self.slot_x(index), ARRAY_Y, 0])
        c.play(
            self.moved(self.key, self.slot_x(index), KEY_Y, KEY),
            FadeIn(self.hole),
            p=ACTION_P,
            cap=1.4,
        )

    def compare(self, c: BeatClock, index: int, bigger: bool):
        """Key (above index+1) against the cell at index. One tick of the counter."""
        sign, colour = (">", SHIFT_COLOR) if bigger else ("<", STOP_COLOR)
        self.relation = MathTex(sign, color=colour).scale(0.9).move_to(
            [self.slot_x(index) + CELL_GAP / 2, (ARRAY_Y + KEY_Y) / 2, 0]
        )
        c.play(
            Indicate(self.slots[index], scale_factor=1.12, color=colour),
            FadeIn(self.relation, scale=0.5),
            self.tick_comparisons(),
            p=ACTION_P,
            cap=1.4,
        )

    def shift(self, c: BeatClock, index: int):
        """Slide slots[index] right into the hole; hole and key step left."""
        cell = self.slots[index]
        self.slots[index + 1], self.slots[index] = cell, None
        c.play(
            self.moved(cell, self.slot_x(index + 1), ARRAY_Y),
            self.hole.animate.move_to([self.slot_x(index), ARRAY_Y, 0]),
            self.key.animate.move_to([self.slot_x(index), KEY_Y, 0]),
            *self.clear_relation(),
            self.tick_shifts(),
            p=ACTION_P,
            cap=1.5,
        )

    def insert(self, c: BeatClock, index: int):
        """Drop the key into the hole; it joins the sorted prefix."""
        key, hole = self.key, self.hole
        self.slots[index] = key
        self.key = self.hole = None
        c.play(
            self.moved(key, self.slot_x(index), ARRAY_Y, SORTED),
            FadeOut(hole),
            *self.clear_relation(),
            p=ACTION_P,
            cap=1.4,
        )

    def sweep_sorted(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.15, color=SORTED[0]) for cell in self.slots),
                lag_ratio=0.25,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def emphasize_counters(self, c: BeatClock):
        c.play(
            Indicate(self.cmp_counter, scale_factor=1.25, color=COUNT_COLOR),
            Indicate(self.shift_counter, scale_factor=1.25, color=COUNT_COLOR),
            p=ACTION_P,
            cap=1.6,
        )

    def formula_tex(self, tex: str, scale: float = 0.8) -> MathTex:
        return MathTex(tex).scale(scale).move_to([0, FORMULA_Y, 0])

    def show_worst(self, c: BeatClock):
        self.formula = self.formula_tex(r"\text{reversed: } 1 + 2 + 3 + 4 = 10 \text{ comparisons}")
        c.play(Write(self.formula), p=ACTION_P, cap=1.8)

    def show_square(self, c: BeatClock):
        nxt = self.formula_tex(r"\text{worst case: } O(n^2)", scale=0.95).set_color(SHIFT_COLOR)
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.6)
        self.formula = nxt

    def show_best(self, c: BeatClock):
        nxt = self.formula_tex(r"\text{nearly sorted: } O(n)", scale=0.95).set_color(STOP_COLOR)
        c.play(FadeTransform(self.formula, nxt), p=ACTION_P, cap=1.6)
        self.formula = nxt

    def fade_out(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(self.array, self.index_labels, self.formula)),
            FadeOut(VGroup(self.title, self.cmp_counter, self.shift_counter)),
            p=ACTION_P,
            cap=2.0,
        )
