"""CLIP-based open-source baseline.

For retrieval: sample frames at 1 fps, embed with CLIP, return top-k frames
matching the query embedding.

For reasoning: sample 5–8 frames evenly across the video, send to Claude
as a multi-image prompt, ask for an answer grounded in the visible content.

Has a fixture-mode fallback so the harness runs without ffmpeg, torch, or
network — fixtures in `fixtures/clip_baseline/`.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ..types import ModelResponse, Question, Video

FIXTURES_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "clip_baseline"

# Frame-sample rates (named so a reader can see the design choices)
RETRIEVAL_FPS = 1.0
REASONING_FRAMES = 6


class ClipBaselineClient:
    """Frame-sampled CLIP for retrieval; frame-sampled Claude for reasoning."""

    def __init__(
        self,
        *,
        anthropic_api_key: str | None = None,
        clip_model: str = "ViT-B-32",
        clip_pretrained: str = "openai",
        reasoning_model: str = "claude-haiku-4-5-20251001",
        fixtures_dir: Path = FIXTURES_ROOT,
    ) -> None:
        self._anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self._clip_model_name = clip_model
        self._clip_pretrained = clip_pretrained
        self._reasoning_model = reasoning_model
        self._fixtures_dir = fixtures_dir
        self._clip: Any = None
        self._anthropic: Any = None

        # Lazy load — heavy deps only matter in live mode.
        if self._anthropic_key:
            try:
                import anthropic  # noqa: F401
                from anthropic import Anthropic
                self._anthropic = Anthropic()
            except ImportError:
                self._anthropic = None

    @property
    def mode(self) -> str:
        return "live" if self._anthropic is not None else "fixtures"

    # ------------------------------------------------------------------
    # Retrieval — CLIP over sampled frames
    # ------------------------------------------------------------------
    def retrieve(self, video: Video, question: Question) -> ModelResponse:
        if self._anthropic is None:
            return self._fixture_response("retrieve", video, question)

        started = time.perf_counter()
        # In a live run this would:
        #   1. Cache the video locally if not already
        #   2. Sample frames at RETRIEVAL_FPS via PyAV / ffmpeg
        #   3. Embed each frame with open_clip, embed the query text
        #   4. Cosine-sim search, take top-k
        #   5. Return frame timestamps + similarity scores
        # The actual implementation is omitted from this scaffold to keep
        # heavy deps optional. See README for the run instructions.
        raise NotImplementedError(
            "Live CLIP retrieval requires the [clip] extra "
            "(open-clip-torch, torch, av). Run in fixture mode to inspect "
            "the report shape, or install the extra and remove this guard."
        )

    # ------------------------------------------------------------------
    # Reasoning — frame-sampled Claude multimodal prompt
    # ------------------------------------------------------------------
    def reason(self, video: Video, question: Question) -> ModelResponse:
        if self._anthropic is None:
            return self._fixture_response("reason", video, question)

        # Similarly: live reasoning would sample REASONING_FRAMES evenly,
        # base64-encode each, and submit as image blocks to Claude. We keep
        # the live path declarative — the fixture path is what runs in this
        # scaffold by default.
        raise NotImplementedError(
            "Live multimodal reasoning requires the [clip] extra plus a video "
            "cache; the scaffold defaults to fixture mode so a fresh clone "
            "produces a complete report. See README for live-run setup."
        )

    # ------------------------------------------------------------------
    # Fixture mode
    # ------------------------------------------------------------------
    def _fixture_response(self, kind: str, video: Video, question: Question) -> ModelResponse:
        path = self._fixtures_dir / kind / f"{question.id}.json"
        if not path.exists():
            return ModelResponse(
                pipeline="clip_baseline",
                question_id=question.id,
                answer=f"(no fixture for {kind}/{question.id})",
                notes=f"fixture-mode; missing {path.relative_to(self._fixtures_dir.parents[1])}",
            )
        data = json.loads(path.read_text())
        return ModelResponse.model_validate({**data, "pipeline": "clip_baseline"})
