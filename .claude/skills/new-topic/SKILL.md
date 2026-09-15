---
name: new-topic
description: Build an AI-teacher topic end to end - sentence-level narration JSON, a TimedScene with caption-first beats, edge-tts with measured timings, both sync checks, then render and mux to rendered/<topic>.mp4. Use when asked to build, add, or create a topic ("build topic 3: quicksort"), or to fix narration/animation sync in an existing one.
---

# Building a topic

Two topics are built this way: `bubble_sort` (35 beats, 149.78s) and
`binary_search` (28 beats, 128.73s). Read either as a worked example --
`scenes/binary_search.py` is the cleaner one. Everything below is the contract
they share; a new topic needs only a name and a visual brief.

## Output contract

```
scripts/<topic>.json    [{id, text, start, end, beat}]  - start/end written by the tool
scenes/<topic>.py       one TimedScene subclass, class name = CamelCase(topic)
audio/<topic>/<id>.mp3  one clip per sentence (+ <id>.txt cache stamp)
audio/<topic>.mp3       concatenated narration master
rendered/<topic>.mp4    1920x1080@30, h264+aac
rendered/manifest.json  {<topic>: {title, category, video, script, scene}} - render_topic adds the entry
```

The class name is derived, not configured: `binary_search` -> `BinarySearch`.
Both `build_topic.py` and `render_topic.py` compute it the same way, so the
file name, the `TOPIC` attribute and the class name must agree.

## Pipeline

```bash
cd /d/ai-teacher
./.venv/Scripts/python.exe tools/build_topic.py  <topic>                      # TTS + timings + BOTH checks
./.venv/Scripts/python.exe tools/render_topic.py <topic> --title "<Title>" --category <category> --quality h --fps 30  # render + mux + list
```

`--title` is the topic's name in the app sidebar. `--category` is the classifier
label a question about it gets: `dynamic_programming`, `math`, `physics`,
`searching`, `sorting` or `stack`. Both are required on a topic's first render
(it exits before rendering without them) and remembered after. Listing the topic
in `rendered/manifest.json` is render_topic's last step, and the app and
`/classify` read that file on every request, so the topic appears on refresh with
no code change and no restart. To list a topic that was rendered before it had an
entry, without rendering it again:
`./.venv/Scripts/python.exe tools/topic_manifest.py <topic> --title "<Title>" --category <category>`

`build_topic.py` exits 1 if either check fails, but only *after* writing the
audio, so a failing check never costs you the TTS run. Never render before it
exits 0 -- the scene reads its run_times out of the timed JSON, and rendering
against untimed JSON silently falls back to `FALLBACK_SLOT` (5s/beat).

Use the venv on D:. Not the global Python, not `D:\manimations\.venv`.

## Step 0 - verify the trace before writing a single sentence

**This is the step that bites.** Binary search for 7 in
`[1, 3, 4, 7, 9, 12, 15, 18]` with the textbook `mid = (lo+hi)//2` on inclusive
bounds terminates on probe 1 -- `(0+7)//2 == 3` and `a[3] == 7`. One probe, no
halving, nothing for a counter to count, and none of the requested visuals
possible. Caught by running the algorithm first; would have cost the entire
narration and a render otherwise.

Run the algorithm on the exact input and print every step. Check that the step
count supports the visual brief. If it does not, say so and choose a fix
explicitly (a different convention, a different input, a different target) --
do not quietly change the spec. For binary search the fix was half-open
`[lo, hi)`, which is standard in `bisect`/`sort.Search` and yields 3 probes with
the window shrinking 8 -> 4 -> 1.

Then write the step list down. It becomes the SCRIPT table one-to-one.

## Step 1 - narration JSON

One beat per **sentence**, one **visible action** per beat. Coarse beats are
what make a video feel out of sync even when timestamps line up: a 20s caption
spans three or four actions, so nothing on screen is tied to the words
describing it.

```json
[
  { "id": 1, "beat": "intro_array", "text": "Here is an array of eight numbers, already in sorted order." },
  { "id": 2, "beat": "intro_sorted", "text": "Sorted is the one thing that binary search absolutely insists on." }
]
```

- `id` unique, `beat` unique, both non-empty -- `load_segments` exits on
  duplicates. Keep ids stable across edits; they name the cached clips.
- `beat` names are the join key to the scene. Prefix by phase
  (`p1_`, `p2_`, `an_`, `end_`) so the table reads in order.
- Optional `caption` overrides what is drawn when the spoken form reads badly
  (`"five, two, nine"` -> `"5, 2, 9"`). Omit it and the caption *is* the
  sentence, minus the trailing period.
- **9-13 words** lands in the 3-6s target at Aria's ~150 wpm. Measured: 7-12
  words -> 3.64-4.99s (bubble), 8-13 -> 3.78-5.13s (binary).
- **ASCII only, and no apostrophes.** Captions render through
  `MathTex(r"\text{...}")`. Both existing scripts are pure ASCII with nothing
  outside alnum, space, comma, colon and hyphen. Write "That is it", not
  "That's it".
- Aim 25-35 segments / 90-150s total.

Sentences are also the caption, so write them to be true *at the moment they
are spoken*. A caption that anticipates the action ("the largest has bubbled to
the end" before the swap) is a defect even when its timestamp is perfect.

## Step 2 - the scene

Copy this skeleton. `make_caption` is byte-identical in both existing topics --
copy it verbatim (a candidate to hoist into `TimedScene` if a third topic wants
it unchanged).

```python
"""<Topic>, animated one narration sentence at a time.

<What is shown. Any non-obvious algorithmic choice, and why it was made.>

Run tools/build_topic.py first; without measured timings the beats fall back to
FALLBACK_SLOT and the video will not line up with the audio.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beat_timing import BeatClock, TimedScene  # noqa: E402

MAX_CAPTION_W = 11.5
ACTION_P = 0.40

# (beat name, action method, args). One row per narration sentence.
SCRIPT = [
    ("intro_array", "reveal_array", ()),
    ("p1_probe",    "probe",        (4,)),
]


class <TopicCamel>(TimedScene):
    TOPIC = "<topic>"
    # STATUS_AT = DOWN * 2.35   # lower the caption when the diagram needs more rows

    def construct(self):
        self.setup_timing()          # first, before any mobject
        ...                          # topic state: values, pointers, counters
        self.build_stage()
        for name, action, args in SCRIPT:
            with self.beat(name) as clock:
                getattr(self, action)(clock, *args)

    def make_caption(self, text: str) -> Mobject:
        mobject = MathTex(r"\text{" + text + "}", color=GREY_A).scale(0.72)
        if mobject.width > MAX_CAPTION_W:
            mobject.scale_to_fit_width(MAX_CAPTION_W)
        return mobject

    def build_stage(self):
        self.title = Text("<Title>", weight=BOLD).scale(0.85).to_edge(UP, buff=0.4)
        self.add(self.title)
        ...                          # build every mobject here; actions only animate

    # --------------------------------------------------------------- actions
    # Each of these issues exactly one c.play: one beat, one visible action.

    def reveal_array(self, c: BeatClock):
        c.play(LaggedStart(...), p=ACTION_P, cap=2.4)
```

Rules that make the checks pass:

- **One `c.play` per action method.** That is what makes "one action per beat"
  structural rather than a thing you have to remember. The audit should show
  exactly 3 steps per beat (caption, action, pause).
- **Never write the caption yourself.** `self.beat(name)` writes it first, from
  the JSON. Calling `set_status` at the top of an action makes the caption late
  and `check_caption_sync` will say so.
- **Chrome rides along inside the action's play** -- pass counters, comparison
  counters. It is not a second action. Two shapes in use: `pass_chrome()`
  (bubble_sort) returns a list to splice in, `counter_tick()` (binary_search)
  returns one `Animation`. Either way it joins the action's existing `c.play`
  rather than adding one.
- **`p=ACTION_P` (0.40) with a `cap`.** Do not compute run_times. The clock
  takes a fraction of the beat and caps it; everything left over becomes the
  trailing pause, so the beat fills its slot exactly whatever the narration
  measures.
- Build mobjects in `build_stage`; actions should only animate what exists.

## Step 3 - the checks

Both run automatically at the end of `build_topic.py`.

`report_beat_lengths` - every beat within 3-6s. An outlier means a sentence is
too long or too clipped; edit the sentence, not the scene. Only the edited
clip re-synthesizes.

`check_caption_sync` - dry-runs the scene with `play`/`wait` stubbed, so it
costs no render. `BeatClock` still accounts every run_time, `TimedScene` logs
`(beat, video_time)` on every caption write, and the first entry per beat must
equal that segment's `start` within 0.05s. It also prints
`scene runs Xs vs narration Ys`, which must be +0.000.

Because the dry run constructs every mobject, it catches `MathTex` syntax
errors, bad kwargs and missing attributes before you burn a render. It cannot
catch layout collisions -- only frames can.

`caption_log` and `video_time` are the public surface these checks read. Do not
rename them.

## Step 4 - render, mux, verify frames

`render_topic.py` renders, muxes with `-shortest`, publishes to
`rendered/<topic>.mp4` and lists it in `rendered/manifest.json`. Then **pull frames and look at them** -- every visual
defect so far was invisible to the checks:

```bash
FF=$(./.venv/Scripts/python.exe -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -loglevel error -ss 80 -i rendered/<topic>.mp4 -frames:v 1 out.png
```

Sample one frame per phase, plus one mid-action frame for anything that moves.

## Layout budget

Frame is 14.22 x 8.0. Observed placements that work:

```
title          to_edge(UP, buff=0.4-0.45), scale 0.85-0.9   (bottom ~y=3.0)
corner badges  to_corner(UL/UR, buff=0.5-0.6)               (target, counters)
diagram        y = +0.8 to +1.25
label row(s)   y = -0.5, second row -1.25
caption        STATUS_AT, default DOWN*1.9; DOWN*2.35 if the diagram needs rows
caption width  <= 11.5, auto-shrunk by make_caption
```

Anything placed between the diagram and the title needs to clear both: the
"found at index 3" label at `ARRAY_Y + 1.5` collided with the title and cost a
render; `ARRAY_Y + 1.05` clears.

When two pointers can share an index (`lo == mid` on the last probe), stagger
them onto different rows rather than hoping they never coincide.

## Gotchas that cost renders

- **Motion arcs cross markers.** A `path_arc=-PI` swap lifts a cell ~0.75 above
  the row; a brace at `buff=0.15` sits at 0.15. Flattening the arc instead makes
  the two moving cells overlap each other. Fix the marker (`buff=0.95`), not the
  arc.
- **Frame quantization.** Manim rounds each animation up to whole frames, so
  video runs ~0.2-0.4s longer than audio over ~100 animations. `-shortest`
  trims it and mid-video lag stays under ~0.2s. Do not chase this unless asked;
  fixing it properly means snapping run_times to the frame grid, which couples
  the scene to render fps and makes the dry run disagree with the render.
- **`max_files_cached = 400` in manim.cfg.** The default 100 evicts partial
  movie files mid-render at this animation count. Do not override `media_dir`
  per-render; it is set in manim.cfg and must stay on D: or dvisvgm fails.
- **No ffprobe on this machine.** Only `imageio_ffmpeg`'s single binary. pydub
  decodes via `AudioSegment.from_file(p, format="mp3", codec="mp3")` (the
  `codec=` argument skips pydub's ffprobe call); durations elsewhere come from
  PyAV. Do not add code that shells out to `ffprobe`.
- **The TTS cache is content-keyed**, via a `<id>.txt` sidecar holding
  voice + exact text. Reusing ids with new text is therefore safe. Do not
  "optimize" it back to an existence check -- that silently reuses stale audio
  and measures timings off the wrong clips, with every check still passing.
- Install packages with `uv pip install --python .venv/Scripts/python.exe <pkg>`.
  There is no `pip` in this venv.

## Checklist

- [ ] Algorithm traced on the exact input; step count supports the visual brief
- [ ] Any spec deviation stated explicitly, with the reason
- [ ] 25-35 sentences, 9-13 words each, ASCII, no apostrophes
- [ ] Unique `id` and `beat`; beats named by phase
- [ ] Every sentence true at the moment it is spoken
- [ ] SCRIPT table matches the traced steps one-to-one
- [ ] Exactly one `c.play` per action method
- [ ] `build_topic.py` exits 0: every beat in target, captions in sync, +0.000
- [ ] Rendered, muxed and listed with `--title` and `--category`; it shows in the app sidebar on refresh
- [ ] Frames sampled per phase and actually looked at
- [ ] Report segment count, total duration, and both check results
