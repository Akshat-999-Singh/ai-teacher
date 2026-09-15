"""What every existing topic draws and how it moves, for choosing a vocabulary that differs.

The new-topic skill's brief step (Step B) runs this before it writes a visual brief for
a topic that arrived with only a name. For each topic in rendered/manifest.json it
parses scenes/<topic>.py (AST only; nothing is run) and prints:

  about       the first paragraph of the scene's docstring
  drawn       Manim mobject classes it constructs (Axes, Square, Arrow, ...)
  motion      animation classes it plays
  .animate    methods it animates through .animate (shift, set_color, ...)
  continuous  anything driven continuously (ValueTracker, add_updater, always_redraw)

Anything every topic uses (captions and titles need Text, MathTex, VGroup, ...) is
printed once at the top and left out of the per-topic lines, so what remains is what
makes each video look like itself. Signature devices (a lifted key, a carved square)
are not class names; read the nearest scenes' docstrings for those.

Usage: .venv\\Scripts\\python.exe tools\\visual_vocab.py [--exclude <topic>]
"""
from __future__ import annotations

import argparse
import ast
import inspect
import sys

import manim

import topic_manifest

ROOT = topic_manifest.ROOT
KINDS = ("drawn", "motion", ".animate", "continuous")
CONTINUOUS = {"ValueTracker", "ComplexValueTracker", "always_redraw", "add_updater",
              "UpdateFromFunc", "UpdateFromAlphaFunc"}


def manim_classes() -> tuple[set[str], set[str]]:
    """Names manim exports that are mobjects, and names that are animations."""
    mobjects, animations = set(), set()
    for name, obj in vars(manim).items():
        if not inspect.isclass(obj):
            continue
        if issubclass(obj, manim.Animation):
            animations.add(name)
        elif issubclass(obj, manim.Mobject):
            mobjects.add(name)
    return mobjects, animations


def about(tree: ast.Module) -> str:
    docstring = ast.get_docstring(tree) or ""
    return " ".join(docstring.split("\n\n")[0].split())


def vocabulary(tree: ast.Module, mobjects: set[str], animations: set[str]) -> dict[str, set[str]]:
    found = {kind: set() for kind in KINDS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name in CONTINUOUS:
                found["continuous"].add(name)
            elif name in animations:
                found["motion"].add(name)
            elif name in mobjects:
                found["drawn"].add(name)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr == "animate":
            found[".animate"].add(node.attr)  # x.animate.shift(...)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the visual vocabulary of every listed topic.")
    parser.add_argument("--exclude", action="append", default=[], metavar="TOPIC",
                        help="leave a topic out, e.g. the one being built")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # titles are not all ASCII; the Windows console default is cp1252

    mobjects, animations = manim_classes()
    scenes = {
        topic: (entry, ast.parse((ROOT / entry["scene"]).read_text(encoding="utf-8")))
        for topic, entry in topic_manifest.read().items()
        if topic not in args.exclude and (ROOT / entry["scene"]).exists()
    }
    if not scenes:
        print("No listed topics with a scene yet: any vocabulary is distinct.")
        return
    vocab = {topic: vocabulary(tree, mobjects, animations) for topic, (_, tree) in scenes.items()}
    shared = {kind: set.intersection(*(v[kind] for v in vocab.values())) for kind in KINDS}

    print(f"Visual vocabularies of {len(scenes)} listed topics (parsed from scenes/, not run)\n")
    for kind in KINDS:
        if shared[kind]:
            print(f"every topic, {kind}: {', '.join(sorted(shared[kind]))}")
    for topic, (entry, tree) in scenes.items():
        print(f"\n{topic} -- {entry['title']} ({entry['category']})")
        print(f"  about:      {about(tree)}")
        for kind in KINDS:
            own = sorted(vocab[topic][kind] - shared[kind])
            print(f"  {kind + ':':<11} {', '.join(own) if own else '-'}")


if __name__ == "__main__":
    main()
