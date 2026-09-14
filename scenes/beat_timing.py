"""Narration-locked beat timing, shared by every topic scene.

The contract is one beat per SENTENCE, not per paragraph. A beat owns a single
narration sentence (target 3-6s), performs exactly one visible action, and
carries that sentence as its caption. Coarser beats are what make a video
"feel" out of sync even when the timestamps line up: a 20s caption covers three
or four actions, so nothing on screen is tied to the words describing it.

A topic scene subclasses `TimedScene`, sets `TOPIC`, and drives a flat list of
(beat, action) pairs. `self.beat(name)` hands the block exactly the wall-clock
slot its sentence occupies in scripts/<topic>.json and writes that sentence's
caption as the block's *first* action, so the caption changes at the instant
the sentence begins.

`tools/build_topic.py` dry-runs a scene against this contract and reports any
beat whose caption is late or whose slot falls outside the target range, so
`caption_log` and `video_time` below are public surface -- do not rename them
without updating that check.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple

from manim import *

ROOT = Path(__file__).resolve().parent.parent

# Used only if a script has not been timed yet, so a scene still renders alone.
FALLBACK_SLOT = 5.0
MIN_RUN_TIME = 1 / 30

# Beats are short now, so the caption needs a fraction big enough to still read
# as a deliberate transition at 3s, and a cap so it stays snappy at 6s.
CAPTION_P = 0.15
CAPTION_CAP = 0.9


class Beat(NamedTuple):
    start: float
    slot: float
    text: str
    caption: str


def load_timeline(topic: str) -> dict[str, Beat]:
    """Map each beat name to its `(start, slot, text, caption)`.

    A beat's slot runs from its own `start` to the *next* beat's `start`, so
    the silence between narration clips belongs to the beat it follows. The
    final beat simply runs to its own `end`. `caption` defaults to the sentence
    itself; a segment may override it where the spoken form reads badly on
    screen (spelled-out numbers, say).
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
        text = seg["text"]
        timeline[seg["beat"]] = Beat(
            start=start,
            slot=slot,
            text=text,
            caption=seg.get("caption") or text.rstrip("."),
        )
    return timeline


class BeatClock:
    """Doles out one beat's duration across the animations inside it.

    Animations ask for a fraction `p` of the beat, capped at a run_time past
    which they would just look sluggish. Time a cap refuses is not lost: it
    goes into `slack`, and the next `hold()` absorbs it. So a beat's spare time
    lands in the pauses *between* its animations instead of piling up as one
    dead stretch at the end.
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
    STATUS_AT = DOWN * 1.9

    def setup_timing(self) -> None:
        """Call first in construct(), before building any mobjects."""
        self.timeline = load_timeline(self.TOPIC)
        self.video_time = 0.0
        self.caption_log: list[tuple[str, float]] = []
        self.current_beat = ""
        self.status = None

    def make_caption(self, text: str) -> Mobject:
        """Render one sentence as the on-screen caption. Override to restyle."""
        return Text(text).scale(0.5)

    @contextmanager
    def beat(
        self,
        name: str,
        caption: str | Mobject | None = None,
        caption_p: float = CAPTION_P,
        caption_cap: float = CAPTION_CAP,
    ):
        """Run one sentence's worth of animation inside that sentence's slot.

        The caption is written before anything else in the block, so it appears
        as the sentence starts. It defaults to the sentence itself, taken from
        the timed script -- one source of truth for what is said and shown.
        """
        info = self.timeline.get(name)
        if info is None:
            raise KeyError(f"beat {name!r} is not in scripts/{self.TOPIC}.json")

        self.current_beat = name
        clock = BeatClock(self, name, info.slot)

        text = info.caption if caption is None else caption
        if text is not None:
            mobject = self.make_caption(text) if isinstance(text, str) else text
            self.set_status(clock, mobject, p=caption_p, cap=caption_cap)

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
