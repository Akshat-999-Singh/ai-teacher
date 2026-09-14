"""Bubble sort, animated one narration sentence at a time.

Every entry in SCRIPT pairs a beat name from scripts/bubble_sort.json with the
single visible action that sentence describes. `self.beat(name)` gives the block
exactly that sentence's slot and writes the sentence as the caption before the
action runs, so caption, narration and motion all start together.

One action per beat is enforced by construction: the driver loop calls exactly
one method per beat, and each of those methods issues exactly one `c.play`.
Chrome that is not part of the array (the pass counter) rides along inside that
same play rather than becoming a second action.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

ARRAY = [5, 2, 9, 1, 7]
CELL_SIZE = 1.1
CELL_GAP = 1.5
MAX_CAPTION_W = 11.5

COMPARE_COLOR = YELLOW
SWAP_COLOR = ORANGE
KEEP_COLOR = TEAL
SORTED_COLOR = GREEN

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_array", "reveal_array", ()),
    ("intro_goal", "sweep_array", ()),
    ("rule_state", "write_rule", ()),
    ("rule_local", "walk_pairs", ()),

    ("p1_cmp01", "mark", (0, 1)),
    ("p1_swap01", "swap", (0,)),
    ("p1_cmp12", "mark", (1,)),
    ("p1_keep12", "keep", (1,)),
    ("p1_cmp23", "mark", (2,)),
    ("p1_swap23", "swap", (2,)),
    ("p1_cmp34", "mark", (3,)),
    ("p1_swap34", "swap", (3,)),

    ("p1_bubbled", "bubbled", ()),
    ("p1_lock", "lock", (4,)),
    ("p1_region", "shrink_region", (4,)),

    ("p2_cmp01", "mark", (0, 2)),
    ("p2_keep01", "keep", (0,)),
    ("p2_cmp12", "mark", (1,)),
    ("p2_swap12", "swap", (1,)),
    ("p2_cmp23", "mark", (2,)),
    ("p2_lock", "lock", (3,)),

    ("p3_cmp01", "mark", (0, 3)),
    ("p3_swap01", "swap", (0,)),
    ("p3_cmp12", "mark", (1,)),
    ("p3_lock", "lock", (2,)),

    ("p4_cmp01", "mark", (0, 4)),
    ("p4_keep", "keep", (0,)),
    ("p4_lock", "lock_rest", ()),

    ("cx_count", "show_counts", ()),
    ("cx_general", "show_general", ()),
    ("cx_bigo", "show_bigo", ()),
    ("cx_double", "emphasize_bigo", ()),

    ("end_slow", "restore_array", ()),
    ("end_worth", "final_sweep", ()),
    ("end_line", "final_line", ()),
]

ACTION_P = 0.40


class BubbleSort(TimedScene):
    TOPIC = "bubble_sort"

    def construct(self):
        self.setup_timing()
        self.values = list(ARRAY)
        self.marked: tuple[int, int] | None = None
        self.brace = None
        self.region = None
        self.pass_label = None

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
        self.title = Text("Bubble Sort", weight=BOLD).scale(0.9).to_edge(UP, buff=0.45)
        self.add(self.title)

        self.slot_pos = [
            RIGHT * (i - (len(ARRAY) - 1) / 2) * CELL_GAP + UP * 0.8
            for i in range(len(ARRAY))
        ]
        self.cells = []
        for value, pos in zip(ARRAY, self.slot_pos):
            square = Square(side_length=CELL_SIZE, stroke_width=4, color=BLUE_B)
            square.set_fill(BLUE_E, opacity=0.25)
            label = MathTex(str(value)).scale(1.1)
            self.cells.append(VGroup(square, label).move_to(pos))
        self.array = VGroup(*self.cells)

        self.rule = MathTex(
            r"a_i > a_{i+1} \;\Rightarrow\; \text{swap them}"
        ).scale(0.75).move_to(DOWN * 3.0)

    def cells_in_slots(self, start: int, stop: int) -> VGroup:
        return VGroup(*self.cells[start:stop])

    def is_locked(self, k: int) -> bool:
        return self.cells[k][0].get_fill_color() == ManimColor(SORTED_COLOR)

    def resting_stroke(self, k: int):
        """Animation returning cell k to the stroke it should wear when idle."""
        colour = SORTED_COLOR if self.is_locked(k) else BLUE_B
        return self.cells[k][0].animate.set_stroke(colour, width=4)

    def pair_brace(self, i: int) -> Brace:
        # buff clears the swap arc's apex (~0.75), so an arcing cell never
        # crosses the marker while the full semicircle keeps the two cells apart.
        brace = Brace(self.cells_in_slots(i, i + 2), UP, buff=0.95)
        return brace.set_color(COMPARE_COLOR)

    def sorted_brace(self, index: int) -> VGroup:
        brace = Brace(self.cells_in_slots(index, len(ARRAY)), DOWN, buff=0.2)
        brace.set_color(SORTED_COLOR)
        text = brace.get_text("sorted").set_color(SORTED_COLOR).scale(0.8)
        return VGroup(brace, text)

    def region_outline(self, upto: int) -> VMobject:
        rect = SurroundingRectangle(
            self.cells_in_slots(0, upto), color=GREY_B, buff=0.22, stroke_width=3
        )
        return DashedVMobject(rect, num_dashes=52)

    def pass_chrome(self, n: int | None) -> list:
        """Pass counter update, folded into whatever play is already running."""
        if n is None:
            return []
        label = Text(f"Pass {n} of 4", weight=BOLD).scale(0.55).set_color(GREY_B)
        label.to_corner(UR, buff=0.6)
        if self.pass_label is None:
            self.pass_label = label
            return [FadeIn(label)]
        anim = FadeTransform(self.pass_label, label)
        self.pass_label = label
        return [anim]

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_array(self, c: BeatClock):
        c.play(
            LaggedStart(*(GrowFromCenter(cell) for cell in self.cells), lag_ratio=0.4),
            p=ACTION_P,
            cap=2.6,
        )

    def sweep_array(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(Indicate(cell, scale_factor=1.12, color=BLUE_B) for cell in self.cells),
                lag_ratio=0.3,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def write_rule(self, c: BeatClock):
        c.play(Write(self.rule), p=ACTION_P, cap=2.0)

    def walk_pairs(self, c: BeatClock):
        """One continuous sweep of the marker across every neighbouring pair."""
        self.marker = self.pair_brace(0)
        steps = [FadeIn(self.marker, shift=DOWN * 0.2)]
        steps += [
            Transform(self.marker, self.pair_brace(i)) for i in range(1, len(ARRAY) - 1)
        ]
        c.play(Succession(*steps), p=ACTION_P + 0.18, cap=3.4)
        self.marked = (len(ARRAY) - 2, len(ARRAY) - 1)

    def mark(self, c: BeatClock, i: int, new_pass: int | None = None):
        """Move the marker onto the pair at slots i, i+1 and light them up."""
        anims = self.pass_chrome(new_pass)
        if self.marked is not None:
            anims += [self.resting_stroke(k) for k in self.marked]
        anims += [
            Transform(self.marker, self.pair_brace(i)),
            self.cells[i][0].animate.set_stroke(COMPARE_COLOR, width=8),
            self.cells[i + 1][0].animate.set_stroke(COMPARE_COLOR, width=8),
        ]
        c.play(*anims, p=ACTION_P, cap=1.4)
        self.marked = (i, i + 1)

    def swap(self, c: BeatClock, i: int):
        j = i + 1
        a, b = self.cells[i], self.cells[j]
        c.play(
            a.animate(path_arc=-PI).move_to(self.slot_pos[j]),
            b.animate(path_arc=-PI).move_to(self.slot_pos[i]),
            p=ACTION_P,
            cap=1.8,
        )
        self.cells[i], self.cells[j] = b, a
        self.values[i], self.values[j] = self.values[j], self.values[i]

    def keep(self, c: BeatClock, i: int):
        """Nothing moves: pulse the pair to show it was checked and left alone."""
        c.play(
            LaggedStart(
                *(
                    Indicate(self.cells[k], scale_factor=1.1, color=KEEP_COLOR)
                    for k in (i, i + 1)
                ),
                lag_ratio=0.35,
            ),
            p=ACTION_P,
            cap=1.8,
        )

    def bubbled(self, c: BeatClock):
        c.play(
            Circumscribe(self.cells[len(ARRAY) - 1], color=SORTED_COLOR, buff=0.12),
            p=ACTION_P + 0.10,
            cap=2.2,
        )

    def lock(self, c: BeatClock, index: int):
        """Settle the cell at `index`, growing the sorted brace to cover it."""
        square = self.cells[index][0]
        anims = [square.animate.set_fill(SORTED_COLOR, opacity=0.35).set_stroke(SORTED_COLOR, width=4)]

        new_brace = self.sorted_brace(index)
        if self.brace is None:
            self.brace = new_brace
            anims.append(FadeIn(new_brace, shift=UP * 0.2))
        else:
            anims.append(Transform(self.brace, new_brace))

        # From pass two on, the region shrinks in the same motion as the lock.
        if self.region is not None and index >= 2:
            anims.append(Transform(self.region, self.region_outline(index)))

        c.play(*anims, p=ACTION_P, cap=1.6)
        self.marked = None

    def shrink_region(self, c: BeatClock, upto: int):
        outline = self.region_outline(upto)
        if self.region is None:
            self.region = outline
            c.play(Create(outline), p=ACTION_P, cap=1.8)
        else:
            c.play(Transform(self.region, outline), p=ACTION_P, cap=1.8)

    def lock_rest(self, c: BeatClock):
        """The last two cells settle together; the working region disappears."""
        anims = [
            self.cells[k][0]
            .animate.set_fill(SORTED_COLOR, opacity=0.35)
            .set_stroke(SORTED_COLOR, width=4)
            for k in (0, 1)
        ]
        anims.append(Transform(self.brace, self.sorted_brace(0)))
        if self.region is not None:
            anims.append(FadeOut(self.region))
            self.region = None
        c.play(*anims, p=ACTION_P, cap=1.8)
        self.marked = None

    def show_counts(self, c: BeatClock):
        """Clear the walkthrough chrome and put the comparison count on screen."""
        self.counts = MathTex(r"4 \;+\; 3 \;+\; 2 \;+\; 1 \;=\; 10").scale(0.9)
        self.counts.move_to(UP * 0.2)
        c.play(
            FadeOut(self.brace),
            FadeOut(self.rule),
            FadeOut(self.marker),
            FadeOut(self.pass_label),
            self.array.animate.scale(0.7).move_to(UP * 1.9),
            Write(self.counts),
            p=ACTION_P,
            cap=1.8,
        )
        self.brace = self.pass_label = None

    def show_general(self, c: BeatClock):
        self.general = MathTex(r"\frac{n(n-1)}{2}").scale(0.95).move_to(UP * 0.2)
        c.play(FadeTransform(self.counts, self.general), p=ACTION_P, cap=1.8)

    def show_bigo(self, c: BeatClock):
        self.big_o = MathTex(r"O(n^2)", color=YELLOW).scale(1.4).move_to(DOWN * 0.9)
        c.play(Write(self.big_o), p=ACTION_P, cap=1.8)

    def emphasize_bigo(self, c: BeatClock):
        c.play(Circumscribe(self.big_o, color=YELLOW, buff=0.2), p=ACTION_P, cap=2.0)

    def restore_array(self, c: BeatClock):
        c.play(
            FadeOut(VGroup(self.general, self.big_o)),
            self.array.animate.scale(1 / 0.7).move_to(UP * 0.6),
            p=ACTION_P,
            cap=1.8,
        )

    def final_sweep(self, c: BeatClock):
        c.play(
            LaggedStart(
                *(
                    Indicate(cell, scale_factor=1.12, color=SORTED_COLOR)
                    for cell in self.cells
                ),
                lag_ratio=0.3,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def final_line(self, c: BeatClock):
        c.play(FadeOut(VGroup(self.array, self.title)), p=ACTION_P, cap=2.0)
