# AI Teacher

Manim + narration pipeline. Deadline: tomorrow 11pm.

## Hard constraints
- Everything stays on D:. Project and media_dir must be on the same
  drive or LaTeX/dvisvgm fails.
- media_dir is set in manim.cfg — do not override it per-render.
- LaTeX is installed; MathTex is available and preferred.
- No Docker, no WSL. Sandbox generated code with subprocess + timeout.
- No LLM API key. Generation happens here, at development time.
- Use the .venv in this folder (Python 3.12). Not the global Python,
  and not the venv in D:\manimations.

## Structure
scenes/ scripts/ audio/ rendered/ data/ frontend/

## Output contract per topic
- scenes/<topic>.py  — Manim scene
- scripts/<topic>.json — [{id, text, start, end, beat}]
- rendered/<topic>.mp4

## Caption rules
- A beat's opening caption must match that segment's FIRST sentence,
  not its conclusion. The payoff line goes at the payoff moment, not
  at the start of the beat.
  Example: segment 5's caption opens "one more comparison: nine
  against seven", NOT "the largest has bubbled to the end" — the 9
  hasn't moved yet. Re-show the payoff caption after the swap.
- A caption must never assert something the animation hasn't shown yet.
- Captions are written by self.beat(name, caption) in TimedScene, which
  guarantees caption-first. Don't write captions any other way.
- Run check_caption_sync() before rendering. It dry-runs the scene with
  play/wait stubbed, so it costs no render time.

  - The caption band is reserved. check_caption_band enforces this, but it
  only catches duplicated text at close range — a different mobject
  overlapping the caption will pass. Keep the band clear by construction.
- Checks verify timing and text, not layout. A scene can pass every check
  and still look wrong. Always view a frame from the middle and end of a
  new scene before calling it done.