"""rendered/manifest.json: which topics are published, under what name and category.

A topic is published when tools/render_topic.py has muxed rendered/<topic>.mp4. Its
last step lists the topic here, with the two things no other pipeline file records:

  title     the display name in the app sidebar ("Insertion sort")
  category  the classifier label that retrieves it for a question (one of CATEGORIES)

This file is the only list of topics. The Vite dev server (frontend/vite.config.js, for
the sidebar) and tools/classify_api.py (for retrieval) both read it on every request and
skip entries whose video or script is missing, so a newly rendered topic shows up on
refresh and a deleted one disappears, with no code change and no restart. Entry order is
sidebar order; a new topic is appended.

List a topic that is already rendered, without rendering it again, or unlist one:
    .venv\\Scripts\\python.exe tools\\topic_manifest.py <topic> --title "Insertion sort" --category sorting
    .venv\\Scripts\\python.exe tools\\topic_manifest.py <topic> --remove
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "rendered" / "manifest.json"

# The labels models/classifier.pkl predicts (v2). A topic filed under any other category
# would be listed but could never be retrieved by a question.
CATEGORIES = ("dynamic_programming", "math", "physics", "searching", "sorting", "stack")


def read() -> dict[str, dict]:
    """Every entry, in sidebar order, whether or not its files still exist."""
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def published() -> dict[str, dict]:
    """Entries whose video and narration script both exist. vite.config.js applies the same rule."""
    return {
        topic: entry for topic, entry in read().items()
        if (ROOT / entry["video"]).exists() and (ROOT / entry["script"]).exists()
    }


def listing(topic: str, title: str | None = None, category: str | None = None) -> tuple[str, str]:
    """The title and category to list a topic under: the arguments, else its current entry.

    Raises ValueError when either is missing or the category is not a classifier label.
    render_topic.py calls this before rendering, so the mistake costs seconds, not a render.
    """
    entry = read().get(topic, {})
    title = (title or entry.get("title") or "").strip()
    category = category or entry.get("category")
    missing = [flag for flag, value in (("--title", title), ("--category", category)) if not value]
    if missing:
        raise ValueError(
            f"{topic!r} is not listed in {MANIFEST.relative_to(ROOT).as_posix()} yet, so pass "
            f"{' and '.join(missing)}: the app sidebar shows the title, and the classifier "
            f"retrieves the topic by category ({', '.join(CATEGORIES)})."
        )
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {', '.join(CATEGORIES)}; got {category!r}")
    return title, category


def register(topic: str, title: str | None = None, category: str | None = None) -> dict:
    """List a rendered topic, or change its title or category. Other fields in its entry are kept."""
    title, category = listing(topic, title, category)
    paths = {"video": f"rendered/{topic}.mp4", "script": f"scripts/{topic}.json", "scene": f"scenes/{topic}.py"}
    absent = [paths[key] for key in ("video", "script") if not (ROOT / paths[key]).exists()]
    if absent:
        raise ValueError(f"cannot list {topic!r}, missing {' and '.join(absent)}; build and render it first")

    manifest = read()
    manifest[topic] = {**manifest.get(topic, {}), "title": title, "category": category, **paths}
    _write(manifest)
    return manifest[topic]


def update(topic: str, **fields) -> dict:
    """Add fields to a listed topic's entry; generate_animation.py records how it was made."""
    manifest = read()
    if topic not in manifest:
        raise KeyError(f"{topic!r} is not listed in {MANIFEST.relative_to(ROOT).as_posix()}")
    manifest[topic].update(fields)
    _write(manifest)
    return manifest[topic]


def unregister(topic: str) -> None:
    manifest = read()
    if manifest.pop(topic, None) is not None:
        _write(manifest)


def _write(manifest: dict) -> None:
    # Written whole and swapped in, so the dev server never reads half a file.
    staging = MANIFEST.with_name(MANIFEST.name + ".tmp")
    staging.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    staging.replace(MANIFEST)


def main() -> None:
    parser = argparse.ArgumentParser(description="List a rendered topic in the app and the classifier, or unlist it.")
    parser.add_argument("topic", help="topic name, e.g. insertion_sort")
    parser.add_argument("--title", help="display name in the app sidebar")
    parser.add_argument("--category", choices=CATEGORIES, help="classifier category that retrieves the topic")
    parser.add_argument("--remove", action="store_true", help="unlist the topic; its files are left alone")
    args = parser.parse_args()

    if args.remove:
        unregister(args.topic)
        print(f"{args.topic}: not listed")
        return
    try:
        entry = register(args.topic, args.title, args.category)
    except ValueError as exc:
        sys.exit(str(exc))
    print(f"{args.topic}: listed as {entry['title']!r} ({entry['category']})")


if __name__ == "__main__":
    main()
