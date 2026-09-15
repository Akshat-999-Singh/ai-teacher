"""BFS and DFS side by side on one 7-node graph, one node visit per sentence.

Same contract as binary_search: every entry in SCRIPT pairs a beat name from
scripts/bfs_dfs.json with the single visible action that sentence describes,
and `self.beat(name)` writes the sentence as the caption first.

The graph is drawn twice, BFS on the left and DFS on the right, and the two
searches take turns so each sentence is one visit on one side. Both run the
same loop -- pop, visit, push unseen neighbors in ascending order, mark on
push -- so the frontier container is the only difference. That is also why DFS
takes the right branch first: 3 is pushed after 2, so it is on top. On this
tree the stack order 1, 3, 7, 6, 2, 5, 4 equals recursive DFS, so marking on
push costs nothing in correctness.

The queue is left-aligned and leaves on the left; the stack is right-aligned
and both enters and leaves on the right. Each exit is fixed, and marked by an
arrow, so where the next node comes from never moves.

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

EDGES = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]
ADJ = {n: sorted({b for a, b in EDGES if a == n} | {a for a, b in EDGES if b == n}) for n in range(1, 8)}

PANEL_X = 3.55
HEADER_Y = 2.45
LEVEL_Y = (1.7, 0.75, -0.2)
LAYOUT = {
    1: (0.0, LEVEL_Y[0]),
    2: (-1.3, LEVEL_Y[1]), 3: (1.3, LEVEL_Y[1]),
    4: (-1.95, LEVEL_Y[2]), 5: (-0.65, LEVEL_Y[2]), 6: (0.65, LEVEL_Y[2]), 7: (1.95, LEVEL_Y[2]),
}
LEVELS = ([1], [2, 3], [4, 5, 6, 7])
NODE_R = 0.27

FRONTIER_Y = -1.2
SLOT = 0.55
STEP = 0.66
CAPACITY = 4  # BFS peaks at [4, 5, 6, 7]
PAD = 0.12

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

UNSEEN = GREY_B
EDGE_COLOR = GREY_D
FRONTIER_COLOR = TEAL
VISITED_COLOR = ORANGE
EXIT_COLOR = YELLOW
SIDE_COLOR = {"bfs": BLUE_B, "dfs": PURPLE_B}

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_graph", "reveal_graphs", ()),
    ("intro_sides", "show_headers", ()),
    ("intro_frontier", "show_frontiers", ()),
    ("intro_exits", "show_exits", ()),
    ("intro_seed", "seed", ()),

    ("v1_bfs", "visit", ("bfs", 1)),
    ("v1_dfs", "visit", ("dfs", 1)),
    ("v2_bfs", "visit", ("bfs", 2)),
    ("v2_dfs", "visit", ("dfs", 3)),
    ("v3_bfs", "visit", ("bfs", 3)),
    ("v3_dfs", "visit", ("dfs", 7)),
    ("v4_bfs", "visit", ("bfs", 4)),
    ("v4_dfs", "visit", ("dfs", 6)),
    ("v5_bfs", "visit", ("bfs", 5)),
    ("v5_dfs", "visit", ("dfs", 2)),
    ("v6_bfs", "visit", ("bfs", 6)),
    ("v6_dfs", "visit", ("dfs", 5)),
    ("v7_bfs", "visit", ("bfs", 7)),
    ("v7_dfs", "visit", ("dfs", 4)),

    ("an_same", "emphasize_containers", ()),
    ("an_bfs_order", "show_order", ("bfs",)),
    ("an_dfs_order", "show_order", ("dfs",)),
    ("an_levels", "sweep_levels", ()),
    ("an_branch", "trace_branch", ((1, 3, 7),)),
    ("an_cost", "show_cost", ()),
    ("end_line", "fade_out", ()),
]


class Side:
    """One panel: a copy of the graph plus its frontier. Not a Mobject."""

    def __init__(self, kind: str, cx: float):
        self.kind = kind
        self.cx = cx
        self.is_queue = kind == "bfs"
        self.exit_dir = LEFT if self.is_queue else RIGHT
        self.nodes: dict[int, VGroup] = {}
        self.edges: dict[tuple[int, int], Line] = {}
        self.values: list[int] = []   # frontier contents, oldest first
        self.cells: list[VGroup] = []  # parallel to values
        self.seen: set[int] = set()
        self.order: list[int] = []
        self.order_row = None


class BfsDfs(TimedScene):
    TOPIC = "bfs_dfs"
    STATUS_AT = DOWN * 2.35

    def construct(self):
        self.setup_timing()
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
        self.title = Text("Graph Traversal", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)
        self.sides = {"bfs": self.build_side("bfs", -PANEL_X), "dfs": self.build_side("dfs", PANEL_X)}

    def build_side(self, kind: str, cx: float) -> Side:
        side = Side(kind, cx)
        side.header = Text(kind.upper(), weight=BOLD).scale(0.6).set_color(SIDE_COLOR[kind])
        side.header.move_to([cx, HEADER_Y, 0])

        for n, (dx, y) in LAYOUT.items():
            circle = Circle(radius=NODE_R, stroke_width=4, color=UNSEEN).set_fill(BLACK, opacity=1)
            side.nodes[n] = VGroup(circle, MathTex(str(n)).scale(0.6)).move_to([cx + dx, y, 0])
        for a, b in EDGES:
            side.edges[(a, b)] = Line(
                side.nodes[a].get_center(), side.nodes[b].get_center(),
                buff=NODE_R, stroke_width=4, color=EDGE_COLOR,
            )

        width = (CAPACITY - 1) * STEP + SLOT + 2 * PAD
        side.rect = RoundedRectangle(
            width=width, height=SLOT + 0.2, corner_radius=0.08, color=GREY_C, stroke_width=3
        ).move_to([cx, FRONTIER_Y, 0])
        side.name = Text("queue" if side.is_queue else "stack").scale(0.42).set_color(GREY_B)
        side.name.next_to(side.rect, RIGHT if side.is_queue else LEFT, buff=0.15)
        edge = side.rect.get_left() if side.is_queue else side.rect.get_right()
        side.arrow = Arrow(
            edge + side.exit_dir * 0.05, edge + side.exit_dir * 0.75, buff=0,
            stroke_width=5, max_tip_length_to_length_ratio=0.35, color=EXIT_COLOR,
        )
        return side

    def slot_positions(self, side: Side, n: int) -> list[np.ndarray]:
        """Queue fills from the left edge, stack from the right: each exit stays put."""
        left = side.rect.get_left()[0] + PAD + SLOT / 2
        right = side.rect.get_right()[0] - PAD - SLOT / 2
        xs = [left + i * STEP for i in range(n)] if side.is_queue else [right - (n - 1 - i) * STEP for i in range(n)]
        return [np.array([x, FRONTIER_Y, 0]) for x in xs]

    def make_cell(self, value: int, at: np.ndarray) -> VGroup:
        square = Square(side_length=SLOT, stroke_width=3, color=FRONTIER_COLOR)
        square.set_fill(TEAL_E, opacity=0.5)
        return VGroup(square, MathTex(str(value)).scale(0.55)).move_to(at)

    def restyled(self, node: VGroup, stroke, fill=None, label=None) -> Animation:
        target = node.copy()
        target[0].set_stroke(stroke, width=4)
        if fill is not None:
            target[0].set_fill(fill, opacity=0.9)
        if label is not None:
            target[1].set_color(label)
        return Transform(node, target)

    def discover(self, side: Side, parent: int, children: list[int]) -> list[Animation]:
        """Push children onto the frontier (positions assume the pop already happened)."""
        side.seen.update(children)
        final = self.slot_positions(side, len(side.values) + len(children))
        anims = []
        for child, at in zip(children, final[len(side.values):]):
            cell = self.make_cell(child, at)
            side.values.append(child)
            side.cells.append(cell)
            anims.append(FadeIn(cell, shift=DOWN * 0.3))
            anims.append(self.restyled(side.nodes[child], FRONTIER_COLOR))
            key = (min(parent, child), max(parent, child))
            anims.append(side.edges[key].animate.set_stroke(FRONTIER_COLOR, width=5))
        return anims

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_graphs(self, c: BeatClock):
        sides = self.sides.values()
        c.play(
            LaggedStart(
                *(GrowFromCenter(s.nodes[n]) for s in sides for n in LAYOUT),
                *(Create(line) for s in sides for line in s.edges.values()),
                lag_ratio=0.06,
            ),
            p=ACTION_P,
            cap=2.4,
        )

    def show_headers(self, c: BeatClock):
        c.play(*(FadeIn(s.header, shift=DOWN * 0.2) for s in self.sides.values()), p=ACTION_P, cap=1.4)

    def show_frontiers(self, c: BeatClock):
        c.play(
            *(Create(s.rect) for s in self.sides.values()),
            *(FadeIn(s.name) for s in self.sides.values()),
            p=ACTION_P,
            cap=1.6,
        )

    def show_exits(self, c: BeatClock):
        c.play(*(GrowArrow(s.arrow) for s in self.sides.values()), p=ACTION_P, cap=1.4)

    def seed(self, c: BeatClock):
        anims = []
        for side in self.sides.values():
            side.seen.add(1)
            cell = self.make_cell(1, self.slot_positions(side, 1)[0])
            side.values, side.cells = [1], [cell]
            anims += [FadeIn(cell, shift=DOWN * 0.3), self.restyled(side.nodes[1], FRONTIER_COLOR)]
        c.play(*anims, p=ACTION_P, cap=1.4)

    def visit(self, c: BeatClock, kind: str, expected: int):
        """Pop from this side's exit, visit that node, then push its unseen neighbors."""
        side = self.sides[kind]
        at = 0 if side.is_queue else -1
        node, cell = side.values.pop(at), side.cells.pop(at)
        if node != expected:  # SCRIPT disagrees with the algorithm: fail the dry run
            raise AssertionError(f"{kind} pops {node}, SCRIPT expects {expected}")
        side.order.append(node)

        children = [m for m in ADJ[node] if m not in side.seen]
        # Remaining cells go straight to where they sit after the push, so the
        # stack never slides right on the pop only to slide back left.
        final = self.slot_positions(side, len(side.values) + len(children))
        pop = AnimationGroup(
            FadeOut(cell, shift=side.exit_dir * 0.7),
            *(rest.animate.move_to(p) for rest, p in zip(side.cells, final)),
            self.restyled(side.nodes[node], VISITED_COLOR, fill=VISITED_COLOR, label=BLACK),
            Flash(side.nodes[node], color=VISITED_COLOR, line_length=0.15, flash_radius=NODE_R + 0.12),
        )
        steps = [pop]
        if children:
            steps.append(AnimationGroup(*self.discover(side, node, children)))
        c.play(Succession(*steps), p=ACTION_P, cap=2.0)

    def emphasize_containers(self, c: BeatClock):
        c.play(
            *(Indicate(s.name, scale_factor=1.3, color=EXIT_COLOR) for s in self.sides.values()),
            *(Indicate(s.rect, scale_factor=1.05, color=EXIT_COLOR) for s in self.sides.values()),
            p=ACTION_P,
            cap=1.6,
        )

    def show_order(self, c: BeatClock, kind: str):
        """The frontier is empty now, so the visit order takes its place."""
        side = self.sides[kind]
        side.order_row = MathTex(
            r"\text{order: } " + r",\ ".join(str(n) for n in side.order), color=SIDE_COLOR[kind]
        ).scale(0.75).move_to([side.cx, FRONTIER_Y, 0])
        c.play(
            FadeOut(VGroup(side.rect, side.name, side.arrow)),
            Write(side.order_row),
            p=ACTION_P,
            cap=1.8,
        )

    def sweep_levels(self, c: BeatClock):
        side = self.sides["bfs"]
        c.play(
            LaggedStart(
                *(
                    Indicate(VGroup(*(side.nodes[n] for n in level)), scale_factor=1.2, color=SIDE_COLOR["bfs"])
                    for level in LEVELS
                ),
                lag_ratio=0.5,
            ),
            p=ACTION_P,
            cap=2.2,
        )

    def trace_branch(self, c: BeatClock, path: tuple[int, ...]):
        side = self.sides["dfs"]
        steps = [Indicate(side.nodes[path[0]], scale_factor=1.25, color=SIDE_COLOR["dfs"])]
        for a, b in zip(path, path[1:]):
            steps.append(Indicate(side.edges[(min(a, b), max(a, b))], scale_factor=1.0, color=SIDE_COLOR["dfs"]))
            steps.append(Indicate(side.nodes[b], scale_factor=1.25, color=SIDE_COLOR["dfs"]))
        c.play(LaggedStart(*steps, lag_ratio=0.4), p=ACTION_P, cap=2.2)

    def show_cost(self, c: BeatClock):
        self.formula = MathTex(r"O(V + E)", color=EXIT_COLOR).scale(1.1).move_to([0, FRONTIER_Y, 0])
        c.play(
            *(FadeOut(s.order_row) for s in self.sides.values()),
            Write(self.formula),
            p=ACTION_P,
            cap=1.8,
        )

    def fade_out(self, c: BeatClock):
        c.play(
            *(
                FadeOut(VGroup(s.header, *s.nodes.values(), *s.edges.values()))
                for s in self.sides.values()
            ),
            FadeOut(VGroup(self.title, self.formula)),
            p=ACTION_P,
            cap=2.0,
        )
