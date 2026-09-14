"""Synthesize narration for a topic, measure it, and time-stamp the script.

Usage:
    python tools/build_topic.py <topic> [--voice VOICE] [--gap SECONDS] [--force]

Reads   scripts/<topic>.json   -> [{id, text, beat}, ...]
Writes  audio/<topic>/<id>.mp3 -> one clip per segment
        audio/<topic>.mp3      -> the segments concatenated, in order
        scripts/<topic>.json   -> same list, now with measured start/end

Timing contract
---------------
`start`/`end` bracket the *speech* of a segment, measured from the real mp3.
A short silence (--gap) is inserted between segments in the concatenated
master, so the next segment's `start` is `end + gap`. That makes the slot a
beat occupies `next.start - this.start`, and the master's total duration
exactly `segments[-1].end`. The Manim scene derives its run_times from those
same numbers, which is what keeps picture and narration locked together.

Topic-agnostic: nothing here knows about any particular topic.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import edge_tts
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
AUDIO = ROOT / "audio"
SCENES = ROOT / "scenes"

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_GAP = 0.35
MAX_TTS_ATTEMPTS = 3
TTS_CONCURRENCY = 4

# A caption may lag its narration by at most this much before it reads as wrong.
CAPTION_TOLERANCE = 0.05

# One sentence per beat, one action per beat. Outside this range a beat is
# either too coarse to tie an action to its sentence, or too clipped to read.
BEAT_MIN, BEAT_MAX = 3.0, 6.0


def _resolve_ffmpeg() -> str:
    """Point pydub at an ffmpeg binary, preferring the one vendored in the venv."""
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        from shutil import which

        exe = which("ffmpeg")
        if not exe:
            sys.exit("ffmpeg not found. Install it, or `uv pip install imageio-ffmpeg`.")
    AudioSegment.converter = exe
    AudioSegment.ffmpeg = exe
    return exe


def load_segments(topic: str) -> list[dict]:
    path = SCRIPTS / f"{topic}.json"
    if not path.exists():
        sys.exit(f"No script at {path}")
    segments = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(segments, list) or not segments:
        sys.exit(f"{path} must be a non-empty JSON list.")
    seen_ids, seen_beats = set(), set()
    for i, seg in enumerate(segments):
        for key in ("id", "text", "beat"):
            if not seg.get(key) and seg.get(key) != 0:
                sys.exit(f"Segment {i} in {path} is missing a non-empty '{key}'.")
        if seg["id"] in seen_ids:
            sys.exit(f"Duplicate segment id {seg['id']!r} in {path}.")
        if seg["beat"] in seen_beats:
            sys.exit(f"Duplicate beat name {seg['beat']!r} in {path}; beats must be unique.")
        seen_ids.add(seg["id"])
        seen_beats.add(seg["beat"])
    return segments


def _stamp_path(clip_dir: Path, seg: dict) -> Path:
    """Sidecar recording exactly what text+voice produced the cached clip."""
    return clip_dir / f"{seg['id']}.txt"


def _is_cached(clip_dir: Path, seg: dict, voice: str) -> bool:
    """Cached only if the clip exists AND was made from this text, in this voice.

    Keying the cache on the file alone is a trap: edit a sentence and you keep
    the old audio, with timings measured off the wrong clip.
    """
    dest = clip_dir / f"{seg['id']}.mp3"
    stamp = _stamp_path(clip_dir, seg)
    if not (dest.exists() and dest.stat().st_size > 0 and stamp.exists()):
        return False
    return stamp.read_text(encoding="utf-8") == f"{voice}\n{seg['text']}"


async def _synthesize_one(seg: dict, clip_dir: Path, voice: str, force: bool, sem) -> None:
    dest = clip_dir / f"{seg['id']}.mp3"
    if not force and _is_cached(clip_dir, seg, voice):
        print(f"  [{seg['id']:>2}] {seg['beat']:<12} cached")
        return
    async with sem:
        for attempt in range(1, MAX_TTS_ATTEMPTS + 1):
            try:
                tmp = dest.with_suffix(".mp3.part")
                await edge_tts.Communicate(seg["text"], voice).save(str(tmp))
                if tmp.stat().st_size == 0:
                    raise RuntimeError("edge-tts produced an empty file")
                tmp.replace(dest)
                _stamp_path(clip_dir, seg).write_text(
                    f"{voice}\n{seg['text']}", encoding="utf-8"
                )
                print(f"  [{seg['id']:>2}] {seg['beat']:<12} synthesized")
                return
            except Exception as exc:  # noqa: BLE001 - network flakiness is the norm here
                if attempt == MAX_TTS_ATTEMPTS:
                    raise
                print(f"  [{seg['id']:>2}] {seg['beat']:<12} retry {attempt} ({exc})")
                await asyncio.sleep(2 * attempt)


def prune_orphans(segments: list[dict], clip_dir: Path) -> None:
    """Drop clips whose id is no longer in the script, so nothing stale is muxed."""
    keep = {str(seg["id"]) for seg in segments}
    for path in sorted(clip_dir.glob("*")):
        if path.suffix in {".mp3", ".txt"} and path.stem not in keep:
            path.unlink()
            print(f"  pruned {path.name}")


async def synthesize_all(segments: list[dict], clip_dir: Path, voice: str, force: bool) -> None:
    sem = asyncio.Semaphore(TTS_CONCURRENCY)
    await asyncio.gather(
        *(_synthesize_one(seg, clip_dir, voice, force, sem) for seg in segments)
    )


def measure_and_time(segments: list[dict], clip_dir: Path, gap: float) -> list[dict]:
    """Read every clip's true duration and lay the segments out on one timeline."""
    timed, cursor = [], 0.0
    for seg in segments:
        clip = clip_dir / f"{seg['id']}.mp3"
        # codec= lets pydub decode straight through ffmpeg, skipping its ffprobe call.
        audio = AudioSegment.from_file(clip, format="mp3", codec="mp3")
        duration = len(audio) / 1000.0
        entry = {
            "id": seg["id"],
            "text": seg["text"],
            "start": round(cursor, 3),
            "end": round(cursor + duration, 3),
            "beat": seg["beat"],
        }
        if seg.get("caption"):  # optional on-screen override of the sentence
            entry["caption"] = seg["caption"]
        timed.append(entry)
        cursor += duration + gap
    return timed


def concatenate(segments: list[dict], clip_dir: Path, out_path: Path, gap: float) -> float:
    """Join the clips (with `gap` of silence between) into one master mp3."""
    clips = [
        AudioSegment.from_file(clip_dir / f"{seg['id']}.mp3", format="mp3", codec="mp3")
        for seg in segments
    ]
    frame_rate = max(c.frame_rate for c in clips)
    clips = [c.set_frame_rate(frame_rate).set_channels(1) for c in clips]

    silence = AudioSegment.silent(duration=int(gap * 1000), frame_rate=frame_rate)
    master = clips[0]
    for clip in clips[1:]:
        master += silence + clip

    out_path.parent.mkdir(parents=True, exist_ok=True)
    master.export(out_path, format="mp3", bitrate="128k")
    return len(master) / 1000.0


def report_beat_lengths(timed: list[dict]) -> bool:
    """Flag beats outside the one-sentence target, longest first."""
    spans = []
    for i, seg in enumerate(timed):
        nxt = timed[i + 1]["start"] if i + 1 < len(timed) else seg["end"]
        spans.append((seg["beat"], round(nxt - seg["start"], 3)))

    outliers = [(b, s) for b, s in spans if not BEAT_MIN <= s <= BEAT_MAX]
    lengths = [s for _, s in spans]
    print(f"\nBeat lengths ({len(spans)} beats, target {BEAT_MIN}-{BEAT_MAX}s):")
    print(f"  min {min(lengths):.2f}s   mean {sum(lengths) / len(lengths):.2f}s   "
          f"max {max(lengths):.2f}s")
    if not outliers:
        print("  every beat is within target.")
        return True
    print(f"  {len(outliers)} outside target:")
    for beat, span in sorted(outliers, key=lambda x: -x[1]):
        side = "long" if span > BEAT_MAX else "short"
        print(f"    {beat:<14} {span:>6.2f}s  ({side})")
    return False


def check_caption_sync(topic: str, timed: list[dict]) -> bool | None:
    """Report when each beat's caption changes vs when its narration starts.

    Dry-runs scenes/<topic>.py with play()/wait() stubbed out, so it costs no
    render: the scene's BeatClock still advances `video_time`, and TimedScene
    records a (beat, time) pair every time a caption is written. The first
    entry for a beat is when that beat's caption appears on screen, and it must
    match that segment's `start` in the JSON -- otherwise the caption is on
    screen while the narrator is still on the previous sentence.

    Returns True/False, or None if the topic has no scene yet.
    """
    scene_path = SCENES / f"{topic}.py"
    if not scene_path.exists():
        print(f"\nCaption sync: no scenes/{topic}.py yet -- skipped.")
        return None

    class_name = "".join(part.capitalize() for part in topic.split("_"))
    spec = importlib.util.spec_from_file_location(f"_scene_{topic}", scene_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        scene_class = getattr(module, class_name)
    except Exception as exc:  # noqa: BLE001 - report, never fail the audio build
        print(f"\nCaption sync: could not load {class_name} from {scene_path.name} ({exc})")
        return None

    if not hasattr(scene_class, "setup_timing"):
        print(f"\nCaption sync: {class_name} does not subclass TimedScene -- skipped.")
        return None

    # Stub the renderer out: BeatClock still accounts for every run_time.
    probe_class = type(
        f"{class_name}Probe",
        (scene_class,),
        {
            "play": lambda self, *a, **k: None,
            "wait": lambda self, duration=1.0, **k: None,
            "add": lambda self, *a, **k: None,
        },
    )
    probe = object.__new__(probe_class)  # skip Scene.__init__; there is no renderer
    try:
        probe.construct()
    except Exception as exc:  # noqa: BLE001
        print(f"\nCaption sync: dry run of {class_name} failed ({exc})")
        return None

    first_caption: dict[str, float] = {}
    for beat, at in probe.caption_log:
        first_caption.setdefault(beat, at)

    width = max(len(s["beat"]) for s in timed)
    print("\nCaption sync (first caption change per beat vs narration start):")
    print(f"  {'beat':<{width}}  {'narration':>10}  {'caption':>9}  {'delta':>8}")
    ok = True
    for seg in timed:
        beat = seg["beat"]
        if beat not in first_caption:
            print(f"  {beat:<{width}}  {seg['start']:>10.3f}  {'-':>9}  {'MISSING':>8}")
            ok = False
            continue
        at = first_caption[beat]
        delta = at - seg["start"]
        flag = "" if abs(delta) <= CAPTION_TOLERANCE else "   <-- LATE"
        if flag:
            ok = False
        print(f"  {beat:<{width}}  {seg['start']:>10.3f}  {at:>9.3f}  {delta:>+8.3f}{flag}")

    total = probe.video_time
    print(f"\n  scene runs {total:.3f}s vs narration {timed[-1]['end']:.3f}s "
          f"({total - timed[-1]['end']:+.3f}s)")
    print("  captions in sync." if ok
          else f"  CAPTION SYNC FAILED (tolerance {CAPTION_TOLERANCE}s).")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Build narration audio + timings for a topic.")
    parser.add_argument("topic", help="topic name, e.g. bubble_sort")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP,
                        help=f"silence between segments, seconds (default {DEFAULT_GAP})")
    parser.add_argument("--force", action="store_true", help="re-synthesize cached clips")
    args = parser.parse_args()

    ffmpeg = _resolve_ffmpeg()
    print(f"ffmpeg: {ffmpeg}")

    segments = load_segments(args.topic)
    clip_dir = AUDIO / args.topic
    clip_dir.mkdir(parents=True, exist_ok=True)
    prune_orphans(segments, clip_dir)

    print(f"\nSynthesizing {len(segments)} segments as {args.voice}:")
    asyncio.run(synthesize_all(segments, clip_dir, args.voice, args.force))

    print("\nMeasuring:")
    timed = measure_and_time(segments, clip_dir, args.gap)

    script_path = SCRIPTS / f"{args.topic}.json"
    script_path.write_text(json.dumps(timed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    master_path = AUDIO / f"{args.topic}.mp3"
    total = concatenate(segments, clip_dir, master_path, args.gap)

    width = max(len(s["beat"]) for s in timed)
    for seg in timed:
        print(f"  [{seg['id']:>2}] {seg['beat']:<{width}}  "
              f"{seg['start']:>7.3f} -> {seg['end']:>7.3f}  "
              f"({seg['end'] - seg['start']:.3f}s)")

    print(f"\n  {script_path.relative_to(ROOT)}  timings written")
    print(f"  {master_path.relative_to(ROOT)}  {total:.3f}s total")

    # Audio is fully written by now, so a failing check never costs you the build.
    lengths_ok = report_beat_lengths(timed)
    sync_ok = check_caption_sync(args.topic, timed)
    if sync_ok is False or not lengths_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
