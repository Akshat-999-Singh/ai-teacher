"""HTTP front for the problem classifier, for the React app.

POST /classify {"text": "..."} ->
  {category, confidence, topic, low_confidence, candidates: [{category, score, topic}] x2}

POST /generate {"topic": "...", "visual_brief": "..."} -> 202 {job_id, status: "queued"}
GET  /generate/{job_id} -> {status: queued | running | done | failed, video?, attempts?, detail?}
  Both answer 503 "runtime generation disabled — no API key" unless ENABLE_RUNTIME_GENERATION
  is set; tools/generate_animation.py explains why it is off.

Run: .venv\\Scripts\\python.exe tools\\classify_api.py    (serves http://127.0.0.1:8000)
Run it as a script from the project root: models/classifier.pkl references the
sentence_embedder module, which is importable because tools/ is the script's directory.
"""
import os

# The embedding weights are already cached on D: (sentence_embedder.HF_CACHE). Stay offline
# so startup never reaches for the network or the default C: cache.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import json
import pickle
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

import config
import generate_animation as generation
import topic_manifest

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "classifier.pkl"

TOP_K = 2

# Measured on the held-out v2 test split (n=131): top-1 accuracy is 38-40% when the best
# probability is below 0.40, 74% at or above it, and 100% above 0.60.
LOW_CONFIDENCE_BELOW = 0.40

# Topics known to have no video. The model can only answer with one of its six categories,
# so a question about any of these still gets a category -- sometimes confidently. v2's
# labelling made it worse: LeetCode problems tagged both Stack and Linked List were filed
# under stack, so "how do I reverse a linked list" scores stack at 0.50 and would play
# Valid parentheses as a confident match. A mention of any of these forces low_confidence
# whatever the score. Accepted cost: "graph"/"tree" also appear in some maths and physics
# questions ("the graph of y = x^2"), which will be flagged too.
ABSENT_TOPICS = re.compile(
    r"\b(?:linked[\s-]?lists?|graphs?|trees?|bfs|dfs|breadth[\s-]?first|depth[\s-]?first"
    r"|hash[\s-]?maps?|two[\s-]?sum)\b",
    re.IGNORECASE,
)

_state = {}


class ClassifyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=2000)


class Candidate(BaseModel):
    category: str
    score: float
    topic: str | None


class ClassifyResponse(BaseModel):
    category: str
    confidence: float
    topic: str | None
    low_confidence: bool
    candidates: list[Candidate]


def rendered_topic(category, listed):
    # The first published topic in this category, in manifest (sidebar) order.
    return next((topic for topic, entry in listed.items() if entry["category"] == category), None)


@asynccontextmanager
async def lifespan(app):
    with open(MODEL_PATH, "rb") as f:
        pipeline = pickle.load(f)
    pipeline.predict_proba(["warm-up"])  # load the embedding model now, not on the first request
    _state["pipeline"] = pipeline
    yield


app = FastAPI(title="AI Teacher classifier", lifespan=lifespan)


@app.post("/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest):
    pipeline = _state["pipeline"]
    probs = pipeline.predict_proba([request.text])[0]
    classes = pipeline.classes_
    # Read per request, so a newly rendered topic is retrievable without a restart.
    listed = topic_manifest.published()

    candidates = [
        Candidate(category=str(classes[i]), score=round(float(probs[i]), 4),
                  topic=rendered_topic(str(classes[i]), listed))
        for i in np.argsort(probs)[::-1][:TOP_K]
    ]
    best = candidates[0]
    return ClassifyResponse(
        category=best.category,
        confidence=best.score,
        # Retrieval looks past the top category when it has no rendered video.
        topic=next((c.topic for c in candidates if c.topic), None),
        low_confidence=best.score < LOW_CONFIDENCE_BELOW or ABSENT_TOPICS.search(request.text) is not None,
        candidates=candidates,
    )


# ---------------------------------------------------------------- runtime generation

GENERATION_DISABLED = {"enabled": False, "detail": "runtime generation disabled — no API key"}

# One job at a time: each is minutes of CPU rendering, and two would starve each other.
_generation_worker = ThreadPoolExecutor(max_workers=1)
_generation_jobs: dict[str, dict] = {}
_generation_lock = threading.Lock()


class GenerateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    topic: str = Field(pattern=generation.TOPIC_NAME.pattern)
    visual_brief: str = Field(min_length=20, max_length=4000)


def _run_generation_job(job_id: str, topic: str, visual_brief: str) -> None:
    job = _generation_jobs[job_id]
    job["status"] = "running"
    try:
        video, attempts = generation.generate_animation(topic, visual_brief)
    except Exception as exc:  # noqa: BLE001 - the job record is a worker thread's only way to report
        job.update(status="failed", detail=str(exc), attempts=getattr(exc, "attempts", None))
    else:
        job.update(status="done", video=f"/media/rendered/{video.name}", attempts=attempts)


@app.post("/generate", status_code=202)
def generate(payload: dict | None = Body(default=None)):
    # The flag is checked before the body is validated, so a disabled server always says so.
    if not config.ENABLE_RUNTIME_GENERATION:
        return JSONResponse(status_code=503, content=GENERATION_DISABLED)
    try:
        request = GenerateRequest.model_validate(payload or {})
    except ValidationError as exc:
        return JSONResponse(status_code=422, content={"enabled": True, "detail": json.loads(exc.json(include_url=False))})
    try:
        generation.require_api_key()
        generation.validate_new_topic(request.topic)
    except generation.MissingAPIKeyError as exc:
        return JSONResponse(status_code=503, content={"enabled": True, "detail": str(exc)})
    except generation.TopicNameError as exc:
        return JSONResponse(status_code=409, content={"enabled": True, "detail": str(exc)})

    with _generation_lock:
        if any(job["status"] in ("queued", "running") for job in _generation_jobs.values()):
            return JSONResponse(status_code=409, content={"enabled": True, "detail": "a generation job is already running"})
        job_id = uuid.uuid4().hex
        _generation_jobs[job_id] = {"job_id": job_id, "topic": request.topic, "status": "queued"}
        queued = dict(_generation_jobs[job_id])
    _generation_worker.submit(_run_generation_job, job_id, request.topic, request.visual_brief)
    return {"enabled": True, **queued}


@app.get("/generate/{job_id}")
def generation_status(job_id: str):
    if not config.ENABLE_RUNTIME_GENERATION:
        return JSONResponse(status_code=503, content=GENERATION_DISABLED)
    job = _generation_jobs.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"enabled": True, "detail": f"no generation job {job_id}"})
    return {"enabled": True, **job}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
