"""Bubble sort, animated in lockstep with the narration in scripts/bubble_sort.json.

Every `with self.beat("<name>", caption=...)` block is given exactly as much screen
time as the narration segment carrying that beat name, and opens by writing that
segment's caption -- so the caption changes as the narrator starts the sentence it
belongs to. Inside a block, animations ask for a *fraction* of the beat (`p=0.2`)
rather than an absolute run_time, so the picture re-locks automatically if the
narration is ever re-synthesized at a different pace. See scenes/beat_timing.py.

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

COMPARE_COLOR = YELLOW
SWAP_COLOR = ORANGE
KEEP_COLOR = TEAL
SORTED_COLOR = GREEN


def caption(text: str, color=GREY_A) -> MathTex:
    return MathTex(r"\text{" + text + "}", color=color).scale(0.78)


class BubbleSort(TimedScene):
    TOPIC = "bubble_sort"

    def construct(self):
        self.setup_timing()
        self.values = list(ARRAY)
        self.brace = None
        self.pass_label = None
        self.pair_marker = None
        self.region = None

        self.build_stage()
        self.beat_show_array()
        self.beat_explain_rule()
        self.beat_first_compare()
        self.beat_continue_pass()
        self.beat_bubble_to_end()
        self.beat_lock_tail()
        self.beat_second_pass()
        self.beat_third_pass()
        self.beat_final_pass()
        self.beat_complexity()
        self.beat_closing()

    # ------------------------------------------------------------------ setup

    def build_stage(self):
        self.title = Text("Bubble Sort", weight=BOLD).scale(0.9).to_edge(UP, buff=0.45)

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

    def cells_in_slots(self, start: int, stop: int) -> VGroup:
        return VGroup(*self.cells[start:stop])

    # --------------------------------------------------------------- helpers

    def verdict(self, left: int, right: int) -> MathTex:
        swap = left > right
        relation = ">" if swap else "<"
        outcome = r"\text{swap}" if swap else r"\text{already in order}"
        return MathTex(
            str(left) + r" \, " + relation + r" \, " + str(right)
            + r" \;\Rightarrow\; " + outcome,
            color=SWAP_COLOR if swap else KEEP_COLOR,
        ).scale(0.85)

    def highlight(self, clock: BeatClock, i: int, j: int, p: float):
        clock.play(
            self.cells[i][0].animate.set_stroke(COMPARE_COLOR, width=8),
            self.cells[j][0].animate.set_stroke(COMPARE_COLOR, width=8),
            p=p,
            cap=0.6,
        )

    def unhighlight(self, clock: BeatClock, i: int, j: int, p: float):
        anims = []
        for k in (i, j):
            if self.cells[k][0].get_fill_color() == ManimColor(SORTED_COLOR):
                anims.append(self.cells[k][0].animate.set_stroke(SORTED_COLOR, width=4))
            else:
                anims.append(self.cells[k][0].animate.set_stroke(BLUE_B, width=4))
        clock.play(*anims, p=p, cap=0.5)

    def mark_pair(self, clock: BeatClock, i: int, j: int, p: float):
        """Slide the yellow bracket above the array onto the pair under test."""
        marker = Brace(self.cells_in_slots(i, j + 1), UP, buff=0.15)
        marker.set_color(COMPARE_COLOR)
        if self.pair_marker is None:
            self.pair_marker = marker
            clock.play(FadeIn(marker, shift=DOWN * 0.2), p=p, cap=0.9)
        else:
            clock.play(Transform(self.pair_marker, marker), p=p, cap=1.1)

    def compare(self, clock: BeatClock, i: int, *, p_each: float):
        """Walk the marker onto slots i and i+1, caption the verdict, swap if needed."""
        j = i + 1
        left, right = self.values[i], self.values[j]

        self.mark_pair(clock, i, j, p=p_each * 0.18)
        self.highlight(clock, i, j, p=p_each * 0.10)
        self.set_status(clock, self.verdict(left, right), p=p_each * 0.14)
        clock.hold(p=p_each * 0.22, cap=3.5)  # let the viewer read the verdict

        if left > right:
            a, b = self.cells[i], self.cells[j]
            clock.play(
                a.animate(path_arc=-PI).move_to(self.slot_pos[j]),
                b.animate(path_arc=-PI).move_to(self.slot_pos[i]),
                p=p_each * 0.20,
                cap=2.2,
            )
            self.cells[i], self.cells[j] = b, a
            self.values[i], self.values[j] = right, left

        self.unhighlight(clock, i, j, p=p_each * 0.08)
        clock.hold(p=p_each * 0.08, cap=3.0)  # let the new arrangement settle

    def working_region(self, upto: int) -> VMobject:
        """Dashed outline around the slots still in play."""
        rect = SurroundingRectangle(
            self.cells_in_slots(0, upto), color=GREY_B, buff=0.22, stroke_width=3
        )
        return DashedVMobject(rect, num_dashes=52)

    def lock(self, clock: BeatClock, index: int, p: float, cap: float = 1.8):
        """Mark the cell in `index` as settled, grow the sorted brace, shrink the region."""
        square = self.cells[index][0]
        anims = [
            square.animate.set_fill(SORTED_COLOR, opacity=0.35).set_stroke(SORTED_COLOR, width=4)
        ]

        brace = Brace(self.cells_in_slots(index, len(ARRAY)), DOWN, buff=0.2)
        brace.set_color(SORTED_COLOR)
        text = brace.get_text("sorted").set_color(SORTED_COLOR).scale(0.8)
        new_brace = VGroup(brace, text)

        if self.brace is None:
            self.brace = new_brace
            anims.append(FadeIn(new_brace, shift=UP * 0.2))
        else:
            anims.append(Transform(self.brace, new_brace))

        # The region still in play is everything left of the sorted tail.
        if index >= 2:
            new_region = self.working_region(index)
            if self.region is None:
                self.region = new_region
                anims.append(Create(new_region))
            else:
                anims.append(Transform(self.region, new_region))
        elif self.region is not None:
            anims.append(FadeOut(self.region))
            self.region = None

        clock.play(*anims, p=p, cap=cap)

    def set_pass_label(self, clock: BeatClock, n: int, p: float, cap: float = 0.8):
        label = Text("Pass " + str(n) + " of 4", weight=BOLD).scale(0.55).set_color(GREY_B)
        label.to_corner(UR, buff=0.6)
        if self.pass_label is None:
            self.pass_label = label
            clock.play(FadeIn(label), p=p, cap=cap)
        else:
            clock.play(FadeTransform(self.pass_label, label), p=p, cap=cap)
            self.pass_label = label

    # ----------------------------------------------------------------- beats
    #
    # Each beat opens on its caption, so the caption changes exactly when that
    # segment's narration starts. The p= of the first animation after the caption
    # is already reduced by CAPTION_P, so the beat still sums to its slot.

    def beat_show_array(self):
        with self.beat("show_array", caption("an array of five numbers")) as c:
            c.play(Write(self.title), p=0.05, cap=1.8)
            c.hold(p=0.04, cap=2.0)
            c.play(
                LaggedStart(
                    *(GrowFromCenter(cell) for cell in self.cells),
                    lag_ratio=0.4,
                ),
                p=0.20,
                cap=4.0,
            )
            c.hold(p=0.10, cap=3.0)
            goal = MathTex(r"\text{smallest} \;\longrightarrow\; \text{largest}").scale(0.8)
            self.set_status(c, goal, p=0.08, cap=1.0)
            c.hold(p=0.12, cap=3.2)
            c.play(
                LaggedStart(
                    *(Indicate(cell, scale_factor=1.1, color=BLUE_B) for cell in self.cells),
                    lag_ratio=0.3,
                ),
                p=0.12,
                cap=2.6,
            )
            c.hold(p=0.10)

    def beat_explain_rule(self):
        with self.beat("explain_rule", caption("one rule: compare two neighbors")) as c:
            self.rule = MathTex(
                r"a_i > a_{i+1} \;\Rightarrow\; \text{swap them}"
            ).scale(0.8).move_to(DOWN * 2.9)
            c.play(Write(self.rule), p=0.07, cap=2.2)
            c.hold(p=0.08, cap=3.0)

            # Walk a marker across every neighboring pair: the rule is purely local.
            for i in range(len(ARRAY) - 1):
                self.mark_pair(c, i, i + 1, p=0.07)
                c.hold(p=0.05, cap=1.8)
            c.hold(p=0.10, cap=3.0)
            c.play(Indicate(self.rule, scale_factor=1.12, color=COMPARE_COLOR), p=0.08, cap=1.8)
            c.hold(p=0.10)

    def beat_first_compare(self):
        with self.beat("first_compare", caption("start at the left edge")) as c:
            self.set_pass_label(c, 1, p=0.05, cap=0.8)
            self.compare(c, 0, p_each=0.55)
            self.set_status(c, caption("not sorted --- but closer than before"), p=0.07, cap=1.0)
            c.hold(p=0.12, cap=3.2)
            c.play(
                LaggedStart(
                    *(Indicate(self.cells[k], scale_factor=1.1, color=KEEP_COLOR) for k in (0, 1)),
                    lag_ratio=0.4,
                ),
                p=0.08,
                cap=2.0,
            )
            c.hold(p=0.08)

    def beat_continue_pass(self):
        with self.beat("continue_pass", caption("slide one step right and repeat")) as c:
            self.compare(c, 1, p_each=0.38)
            self.compare(c, 2, p_each=0.39)
            c.play(Indicate(self.cells[3], scale_factor=1.12, color=COMPARE_COLOR), p=0.08, cap=1.6)
            c.hold(p=0.10)

    def beat_bubble_to_end(self):
        with self.beat(
            "bubble_to_end", caption("one more comparison: nine against seven")
        ) as c:
            self.compare(c, 3, p_each=0.45)
            c.play(
                Circumscribe(self.cells[4], color=SORTED_COLOR, buff=0.12),
                p=0.12,
                cap=2.2,
            )
            # Only now is this true on screen: 9 has reached the last slot.
            self.set_status(
                c, caption("the largest has bubbled to the end", SORTED_COLOR), p=0.07, cap=1.0
            )
            c.hold(p=0.12, cap=3.2)
            c.play(Indicate(self.cells[4], scale_factor=1.15, color=SORTED_COLOR), p=0.08, cap=1.6)
            c.hold(p=0.11)

    def beat_lock_tail(self):
        with self.beat("lock_tail", caption("nothing left can be larger", SORTED_COLOR)) as c:
            self.lock(c, 4, p=0.14, cap=2.0)
            c.hold(p=0.16, cap=3.2)
            self.set_status(c, caption("working region: 4 cells"), p=0.07, cap=1.0)
            c.hold(p=0.16, cap=3.2)
            c.play(
                Circumscribe(self.cells_in_slots(0, 4), color=GREY_A, buff=0.22),
                p=0.10,
                cap=2.4,
            )
            c.hold(p=0.14)

    def beat_second_pass(self):
        with self.beat("second_pass", caption("pass 2: repeat on what is left")) as c:
            self.set_pass_label(c, 2, p=0.05, cap=0.8)
            for i in range(3):
                self.compare(c, i, p_each=0.24)
            self.lock(c, 3, p=0.10, cap=1.8)
            c.hold(p=0.08)

    def beat_third_pass(self):
        with self.beat("third_pass", caption("each pass is cheaper than the last")) as c:
            self.set_pass_label(c, 3, p=0.05, cap=0.8)
            for i in range(2):
                self.compare(c, i, p_each=0.31)
            self.lock(c, 2, p=0.10, cap=1.8)
            c.hold(p=0.17)

    def beat_final_pass(self):
        with self.beat("final_pass", caption("one final comparison")) as c:
            self.set_pass_label(c, 4, p=0.05, cap=0.8)
            self.compare(c, 0, p_each=0.40)
            self.lock(c, 1, p=0.08, cap=1.6)
            self.lock(c, 0, p=0.08, cap=1.6)
            sorted_chain = MathTex(r"1 < 2 < 5 < 7 < 9", color=SORTED_COLOR).scale(0.9)
            self.set_status(c, sorted_chain, p=0.07, cap=1.0)
            c.hold(p=0.27)

    def beat_complexity(self):
        with self.beat("complexity", caption("step back and count the work")) as c:
            c.play(
                FadeOut(self.brace),
                FadeOut(self.rule),
                FadeOut(self.pass_label),
                FadeOut(self.pair_marker),
                self.array.animate.scale(0.75).shift(UP * 0.6),
                p=0.07,
                cap=1.4,
            )
            self.brace = self.pass_label = self.pair_marker = None

            counts = MathTex(r"4 \;+\; 3 \;+\; 2 \;+\; 1 \;=\; 10").scale(0.9)
            counts.move_to(DOWN * 0.7)
            c.play(Write(counts), p=0.10, cap=2.0)
            c.hold(p=0.12, cap=3.2)

            general = MathTex(r"\frac{n(n-1)}{2} \;\sim\; \frac{n^2}{2}").scale(0.9)
            general.move_to(DOWN * 0.7)
            c.play(FadeTransform(counts, general), p=0.09, cap=1.8)
            c.hold(p=0.12, cap=3.2)

            big_o = MathTex(r"O(n^2)", color=YELLOW).scale(1.5).move_to(DOWN * 2.7)
            c.play(Write(big_o), p=0.09, cap=1.8)
            c.hold(p=0.10, cap=2.6)
            c.play(Circumscribe(big_o, color=YELLOW, buff=0.2), p=0.09, cap=2.0)
            c.hold(p=0.17)
            self.tail_group = VGroup(general, big_o)

    def beat_closing(self):
        with self.beat("closing", caption("too slow for real data")) as c:
            c.play(FadeOut(self.tail_group), p=0.06, cap=1.2)
            c.play(self.array.animate.scale(1 / 0.75).move_to(UP * 0.4), p=0.07, cap=1.6)
            c.hold(p=0.10, cap=2.6)
            c.play(
                LaggedStart(
                    *(
                        Indicate(cell, scale_factor=1.12, color=SORTED_COLOR)
                        for cell in self.cells
                    ),
                    lag_ratio=0.3,
                ),
                p=0.14,
                cap=3.0,
            )
            c.hold(p=0.10, cap=2.6)
            self.set_status(c, None, p=0.04, cap=0.6)
            done = Text("simple rule, applied patiently", slant=ITALIC).scale(0.75)
            done.set_color(GREY_A).move_to(DOWN * 2.0)
            c.play(FadeIn(done, shift=UP * 0.3), p=0.10, cap=1.8)
            c.hold(p=0.15, cap=4.5)
            c.play(FadeOut(VGroup(self.array, done, self.title)), p=0.10, cap=2.2)
            c.hold(p=0.08)
