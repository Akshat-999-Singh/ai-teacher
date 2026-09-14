"""Narration-locked beat timing, shared by every topic scene.

A topic scene subclasses `TimedScene`, sets `TOPIC`, and wraps each group of
animations in `with self.beat("<beat name>", caption=...)`. The beat is handed
exactly the wall-clock slot its narration segment occupies in
scripts/<topic>.json, and its caption is written as the beat's *first* action,
so the caption changes at the instant that segment's narration begins.

Caption placement is a correctness property, not a style choice: a caption
written partway through a beat is on screen while the narrator is still
talking about something else. `tools/build_topic.py` dry-runs a scene against
this contract and reports any beat whose caption is late, so `caption_log` and
`video_time` below are public surface -- do not rename them without updating
that check.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from manim import *

ROOT = Path(__file__).resolve().parent.parent

# Used only if a script has not been timed yet, so a scene still renders alone.
FALLBACK_SLOT = 8.0
MIN_RUN_TIME = 1 / 30

# A beat's opening caption is deliberately cheap: it must land with the
# narration, so it gets a small slice taken out of the beat's first animation.
CAPTION_P = 0.05
CAPTION_CAP = 0.9


def load_timeline(topic: str) -> dict[str, tuple[float, float]]:
    """Map each beat name to `(start, slot)` in seconds.

    A beat's slot runs from its own `start` to the *next* beat's `start`, so
    the silence between narration clips belongs to the beat it follows. The
    final beat simply runs to its own `end`.
    """
    path = ROOT / "scripts" / f"{topic}.json"
    segments = json.loads(path.read_text(encoding="utf-8"))
    timed = all("start" in s and "end" in s for s in segments)

    timeline = {}
    for i, seg in enumerate(segments):
        if timed:
            start = seg["start"]
            nxt = segments[i + 1]["start"] if i + 1 < len(segments) else seg["end"]
            slot = round(nxt - start, 3)
        else:
            start, slot = i * FALLBACK_SLOT, FALLBACK_SLOT
        timeline[seg["beat"]] = (start, slot)
    return timeline


class BeatClock:
    """Doles out one beat's duration across the animations inside it.

    Animations ask for a fraction `p` of the beat, capped at a run_time past
    which they would just look sluggish. Time a cap refuses is not lost: it
    goes into `slack`, and the next `hold()` absorbs it. So a beat's spare time
    lands in the pauses *between* its animations -- where a viewer reads the
    caption you just put on screen -- instead of piling up as one dead stretch
    at the end. Keep sum(p) close to 1.0 and end each beat on a hold.
    """

    def __init__(self, scene: TimedScene, name: str, total: float):
        self.scene = scene
        self.name = name
        self.total = total
        self.remaining = total
        self.elapsed = 0.0
        self.slack = 0.0

    def _take(self, p: float, cap: float | None, elastic: bool) -> float:
        want = self.total * p
        if elastic:
            want += self.slack
            self.slack = 0.0
        if cap is not None and want > cap:
            self.slack += want - cap
            want = cap
        return max(min(want, self.remaining), 0.0)

    def _advance(self, run_time: float) -> None:
        self.elapsed += run_time
        self.remaining -= run_time
        self.scene.video_time += run_time

    def play(self, *animations, p: float, cap: float | None = None, **kwargs) -> None:
        run_time = self._take(p, cap, elastic=False)
        if run_time < MIN_RUN_TIME:
            return
        self.scene.play(*animations, run_time=run_time, **kwargs)
        self._advance(run_time)

    def hold(self, p: float = 0.0, cap: float | None = None) -> None:
        run_time = self._take(p, cap, elastic=True)
        if run_time < MIN_RUN_TIME:
            return
        self.scene.wait(run_time)
        self._advance(run_time)

    def finish(self) -> None:
        """Hold whatever the beat did not spend, so it fills its slot exactly."""
        if self.remaining >= MIN_RUN_TIME:
            run_time = self.remaining
            self.scene.wait(run_time)
            self._advance(run_time)  # same accounting as every other pause
        self.remaining = 0.0


class TimedScene(Scene):
    """Base for topic scenes whose animation is locked to measured narration."""

    TOPIC: str = ""
    STATUS_AT = DOWN * 1.7

    def setup_timing(self) -> None:
        """Call first in construct(), before building any mobjects."""
        self.timeline = load_timeline(self.TOPIC)
        self.video_time = 0.0
        self.caption_log: list[tuple[str, float]] = []
        self.current_beat = ""
        self.status = None

    @contextmanager
    def beat(
        self,
        name: str,
        caption: Mobject | None = None,
        caption_p: float = CAPTION_P,
        caption_cap: float = CAPTION_CAP,
    ):
        """Run a block of animations inside one narration segment's slot.

        `caption` is written before anything else in the block, so it appears
        as the segment's narration starts. Pay for it out of the beat's first
        animation (drop its `p` by `caption_p`), never by adding to the beat.
        """
        _, slot = self.timeline.get(name, (0.0, FALLBACK_SLOT))
        self.current_beat = name
        clock = BeatClock(self, name, slot)
        if caption is not None:
            self.set_status(clock, caption, p=caption_p, cap=caption_cap)
        yield clock
        clock.finish()

    def set_status(self, clock: BeatClock, mobject, p: float, cap: float = 0.9):
        """Swap the caption under the diagram for a new one (or clear it)."""
        if mobject is not None:
            mobject.move_to(self.STATUS_AT)
            # Logged before the transition plays: this is the moment the
            # caption starts changing, which is what must match narration start.
            self.caption_log.append((self.current_beat, round(self.video_time, 3)))

        if self.status is None and mobject is None:
            return
        if self.status is None:
            self.status = mobject
            clock.play(FadeIn(mobject, shift=UP * 0.2), p=p, cap=cap)
        elif mobject is None:
            clock.play(FadeOut(self.status), p=p, cap=cap)
            self.status = None
        else:
            clock.play(FadeTransform(self.status, mobject), p=p, cap=cap)
            self.status = mobject
