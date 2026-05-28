"""Twelve Labs client.

Thin wrapper over the official `twelvelabs` SDK, with a fixture-mode fallback
that lets the harness run end-to-end without API keys or network access. The
fixture mode reads pre-recorded responses from `fixtures/twelve_labs/` so the
report shape is inspectable from a fresh clone.

Notes on SDK shape:
    The Twelve Labs Python SDK has revised its public surface a few times.
    This wrapper targets the post-v0.3 client (`from twelvelabs import
    TwelveLabs`). If you adapt this to a newer SDK, the integration points
    are clearly marked with `# SDK CALL:` comments — adjust those.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ..types import ModelResponse, Question, Video

FIXTURES_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "twelve_labs"


class TwelveLabsClient:
    """Routes calls to either the live Twelve Labs SDK or local fixtures."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        marengo_engine: str = "marengo3.0",
        pegasus_engine: str = "pegasus1.5",
        fixtures_dir: Path = FIXTURES_ROOT,
    ) -> None:
        self._api_key = api_key or os.getenv("TWELVE_LABS_API_KEY")
        self._marengo = marengo_engine
        self._pegasus = pegasus_engine
        self._fixtures_dir = fixtures_dir
        self._live: Any = None
        self._index_cache: dict[str, str] = {}

        if self._api_key:
            try:
                # Lazy import so the harness loads without the SDK installed.
                from twelvelabs import TwelveLabs  # type: ignore[import-not-found]
                self._live = TwelveLabs(api_key=self._api_key)
            except ImportError:
                self._live = None

    @property
    def mode(self) -> str:
        return "live" if self._live is not None else "fixtures"

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    def ensure_indexed(self, video: Video) -> str:
        """Return a video_id usable for downstream search/generate calls."""
        if self._live is None:
            return f"fixture::{video.id}"

        if video.id in self._index_cache:
            return self._index_cache[video.id]

        # SDK CALL: create an index that supports both Marengo and Pegasus.
        index = self._live.index.create(
            name=f"eval-{video.id}",
            engines=[
                {"name": self._marengo, "options": ["visual", "audio"]},
                {"name": self._pegasus, "options": ["visual"]},
            ],
        )

        # SDK CALL: kick off ingest from URL; poll task to completion.
        task = self._live.task.create(index_id=index.id, url=video.url)
        while task.status not in ("ready", "failed"):
            time.sleep(5)
            task = self._live.task.retrieve(task.id)
        if task.status == "failed":
            raise RuntimeError(f"Twelve Labs ingest failed for {video.id}: {task}")

        video_id = task.video_id
        self._index_cache[video.id] = video_id
        return video_id

    # ------------------------------------------------------------------
    # Search (Marengo) — for retrieval-kind questions
    # ------------------------------------------------------------------
    def search(self, video: Video, question: Question) -> ModelResponse:
        if self._live is None:
            return self._fixture_response("search", video, question)

        video_id = self.ensure_indexed(video)
        started = time.perf_counter()
        # SDK CALL: visual + audio retrieval against an indexed video.
        result = self._live.search.query(
            index_id=self._index_for(video),
            query_text=question.prompt,
            options=["visual", "audio"],
            filter={"video_ids": [video_id]},
        )
        latency_ms = int((time.perf_counter() - started) * 1000)

        # Compose a textual answer from top-k clips with timestamps.
        clips = [
            f"[{c.start:.1f}s–{c.end:.1f}s] score={c.score:.2f}"
            for c in result.data[:5]
        ]
        answer = (
            "Top matches:\n" + "\n".join(clips)
            if clips
            else "No matches above threshold."
        )

        return ModelResponse(
            pipeline="twelve_labs",
            question_id=question.id,
            answer=answer,
            citations=[c[:80] for c in clips],
            latency_ms=latency_ms,
            notes=f"Marengo {self._marengo}, top-{len(clips)} clips",
        )

    # ------------------------------------------------------------------
    # Generate (Pegasus) — for reasoning-kind questions
    # ------------------------------------------------------------------
    def generate(self, video: Video, question: Question) -> ModelResponse:
        if self._live is None:
            return self._fixture_response("generate", video, question)

        video_id = self.ensure_indexed(video)
        started = time.perf_counter()
        # SDK CALL: open-ended generation grounded in the indexed video.
        result = self._live.generate.text(
            video_id=video_id,
            prompt=question.prompt,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)

        return ModelResponse(
            pipeline="twelve_labs",
            question_id=question.id,
            answer=result.data,
            latency_ms=latency_ms,
            notes=f"Pegasus {self._pegasus}",
        )

    # ------------------------------------------------------------------
    # Fixture mode
    # ------------------------------------------------------------------
    def _fixture_response(self, kind: str, video: Video, question: Question) -> ModelResponse:
        path = self._fixtures_dir / kind / f"{question.id}.json"
        if not path.exists():
            return ModelResponse(
                pipeline="twelve_labs",
                question_id=question.id,
                answer=f"(no fixture for {kind}/{question.id})",
                notes=f"fixture-mode; missing {path.relative_to(self._fixtures_dir.parents[1])}",
            )
        data = json.loads(path.read_text())
        return ModelResponse.model_validate({**data, "pipeline": "twelve_labs"})

    def _index_for(self, video: Video) -> str:
        # Helper that would map a video to its index id in a real run;
        # in this scaffold we use a single index per video for simplicity.
        return self._index_cache.get(video.id, "")
