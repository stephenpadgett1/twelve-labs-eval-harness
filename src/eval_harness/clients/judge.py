"""LLM-as-judge.

Scores each pipeline's response on three axes (1-5) plus a short rationale.
Uses Claude (default: Sonnet 4.6) for the judge call. Has a deterministic
fixture-mode fallback so the harness runs without an API key.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from ..types import JudgeScore, ModelResponse, Question

FIXTURES_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "judge"

JUDGE_PROMPT = """You are an evaluator for video-understanding model outputs.

Given a question about a video, a reference answer, and a model's response,
score the model's response on three axes (1-5 integer each):

  - relevance: does the response actually address the question?
  - faithfulness: does it stay consistent with the reference answer and avoid
    fabricating content not implied by it?
  - specificity: does it cite concrete moments / details vs hedging?

Then give a 1-2 sentence rationale.

Return strict JSON of the shape:
{{
  "relevance": <int 1-5>,
  "faithfulness": <int 1-5>,
  "specificity": <int 1-5>,
  "rationale": "<string>"
}}

Question: {question}
Reference answer: {expects}
Model response: {answer}
"""


class Judge:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        fixtures_dir: Path = FIXTURES_ROOT,
    ) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._model = model
        self._fixtures_dir = fixtures_dir
        self._anthropic: Any = None
        if self._api_key:
            try:
                from anthropic import Anthropic
                self._anthropic = Anthropic()
            except ImportError:
                self._anthropic = None

    @property
    def mode(self) -> str:
        return "live" if self._anthropic is not None else "fixtures"

    def score(self, question: Question, response: ModelResponse) -> JudgeScore:
        if self._anthropic is None:
            return self._fixture_score(question, response)

        prompt = JUDGE_PROMPT.format(
            question=question.prompt,
            expects=question.expects,
            answer=response.answer,
        )

        result = self._anthropic.messages.create(
            model=self._model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in result.content if getattr(block, "type", None) == "text"
        )
        parsed = self._parse_json(text)
        return JudgeScore(
            question_id=question.id,
            pipeline=response.pipeline,
            relevance=int(parsed["relevance"]),
            faithfulness=int(parsed["faithfulness"]),
            specificity=int(parsed["specificity"]),
            rationale=str(parsed["rationale"]),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        # Defensive: judges occasionally wrap JSON in markdown fencing.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"judge returned non-JSON: {text[:200]!r}")
        return json.loads(match.group(0))

    def _fixture_score(self, question: Question, response: ModelResponse) -> JudgeScore:
        path = self._fixtures_dir / f"{question.id}__{response.pipeline}.json"
        if not path.exists():
            # Deterministic fallback: produce a plausible mid-range score so
            # the report renders even if a fixture is missing.
            return JudgeScore(
                question_id=question.id,
                pipeline=response.pipeline,
                relevance=3,
                faithfulness=3,
                specificity=2,
                rationale=(
                    "(no fixture available; placeholder mid-range score so the "
                    "report still renders. Add fixture or run with ANTHROPIC_API_KEY set.)"
                ),
            )
        data = json.loads(path.read_text())
        return JudgeScore.model_validate({
            **data,
            "question_id": question.id,
            "pipeline": response.pipeline,
        })
