"""Render a topic's Manim scene, mux its narration in, and publish the result.

Usage:
    python tools/render_topic.py <topic> [--title TITLE --category CATEGORY] [--scene CLASS] [--quality h] [--fps 30]

Reads   scenes/<topic>.py       -> Manim scene (class defaults to the CamelCase topic)
        audio/<topic>.mp3       -> narration master from build_topic.py
Writes  rendered/<topic>.mp4    -> silent render + narration, muxed
        rendered/manifest.json  -> the topic's entry, which lists it in the app sidebar
                                   and makes it retrievable by /classify

--title and --category are required on a topic's first render and remembered after it
(tools/topic_manifest.py). Listing is the last step, so a topic appears in the app only
once its video is muxed.

Run build_topic.py first: the scene reads its run_times out of the timed
scripts/<topic>.json, so rendering before timing produces a video that is not
locked to the audio.

Topic-agnostic: nothing here knows about any particular topic.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import topic_manifest

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / "scenes"
AUDIO = ROOT / "audio"
MEDIA = ROOT / "media"
RENDERED = ROOT / "rendered"

RENDER_TIMEOUT = 60 * 60  # a 1080p topic render is minutes, not hours
MUX_TIMEOUT = 10 * 60


def resolve_ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = shutil.which("ffmpeg")
        if not exe:
            sys.exit("ffmpeg not found. Install it, or `uv pip install imageio-ffmpeg`.")
        return exe


def probe_duration(path: Path) -> float:
    """Duration in seconds, read through PyAV so no ffprobe binary is needed."""
    import av

    with av.open(str(path)) as container:
        return container.duration / av.time_base


def default_scene_name(topic: str) -> str:
    return "".join(part.capitalize() for part in topic.split("_"))


def render(topic: str, scene: str, quality: str, fps: int) -> Path:
    scene_file = SCENES / f"{topic}.py"
    if not scene_file.exists():
        sys.exit(f"No scene at {scene_file}")

    # media_dir deliberately not passed: it is fixed in manim.cfg.
    command = [
        sys.executable, "-m", "manim", "render",
        f"-q{quality}", "--fps", str(fps),
        str(scene_file), scene,
    ]
    print("  " + " ".join(command))
    result = subprocess.run(
        command, cwd=ROOT, timeout=RENDER_TIMEOUT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if result.returncode != 0:
        print(result.stdout[-4000:])
        sys.exit(f"manim exited {result.returncode}")

    candidates = sorted(
        (MEDIA / "videos" / topic).rglob(f"{scene}.mp4"),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        sys.exit(f"Render reported success but no {scene}.mp4 found under media/videos/{topic}")
    return candidates[-1]


def mux(video: Path, audio: Path, out_path: Path, ffmpeg: str) -> None:
    """Attach the narration. -shortest trims the frame-quantization tail off the video."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-y",
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]
    result = subprocess.run(
        command, timeout=MUX_TIMEOUT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if result.returncode != 0:
        print(result.stdout[-4000:])
        sys.exit(f"ffmpeg mux exited {result.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a topic and mux its narration in.")
    parser.add_argument("topic", help="topic name, e.g. bubble_sort")
    parser.add_argument("--title", help="display name in the app sidebar; required on the first render")
    parser.add_argument("--category", choices=topic_manifest.CATEGORIES,
                        help="classifier category that retrieves the topic; required on the first render")
    parser.add_argument("--scene", default=None, help="scene class (default: CamelCase topic)")
    parser.add_argument("--quality", default="h", choices=list("lmhpk"),
                        help="manim quality flag (default h = 1080p)")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    # Before the render, so a missing title or category costs seconds rather than a render.
    try:
        title, category = topic_manifest.listing(args.topic, args.title, args.category)
    except ValueError as exc:
        sys.exit(str(exc))

    scene = args.scene or default_scene_name(args.topic)
    audio = AUDIO / f"{args.topic}.mp3"
    if not audio.exists():
        sys.exit(f"No narration at {audio}. Run: python tools/build_topic.py {args.topic}")

    print(f"Rendering {args.topic} ({scene}) at -q{args.quality} {args.fps}fps:")
    silent = render(args.topic, scene, args.quality, args.fps)

    out_path = RENDERED / f"{args.topic}.mp4"
    print(f"\nMuxing {audio.name} into {silent.name}:")
    mux(silent, audio, out_path, resolve_ffmpeg())

    v, a, o = probe_duration(silent), probe_duration(audio), probe_duration(out_path)
    print(f"  silent video : {v:8.3f}s")
    print(f"  narration    : {a:8.3f}s")
    print(f"  drift        : {v - a:+8.3f}s")
    print(f"\n  {out_path.relative_to(ROOT)}  {o:.3f}s")

    try:
        topic_manifest.register(args.topic, title, category)
    except ValueError as exc:
        sys.exit(str(exc))
    print(f"  listed in {topic_manifest.MANIFEST.relative_to(ROOT)} as {title!r} ({category})")


if __name__ == "__main__":
    main()
