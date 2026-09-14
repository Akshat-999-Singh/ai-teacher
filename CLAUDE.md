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