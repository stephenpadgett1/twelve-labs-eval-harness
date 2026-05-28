"""Domain types used across the harness. Pydantic so the JSON fixtures
serialize cleanly and the report writer can rely on shape."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

UseCase = Literal["product_demo", "sports_action", "lecture"]
QuestionKind = Literal["retrieval", "reasoning", "structured"]
Pipeline = Literal["twelve_labs", "clip_baseline"]
Ablation = Literal["none", "visual_only"]


class Video(BaseModel):
    id: str
    title: str
    url: str
    duration_s: int
    use_case: UseCase
    description: str


class Question(BaseModel):
    id: str
    video_id: str
    kind: QuestionKind
    prompt: str
    expects: str
    # Only populated for `structured` questions — the JSON schema Pegasus 1.5
    # Time-Based Metadata extraction will produce against. Left as a plain dict
    # so the YAML stays declarative.
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")

    model_config = {"populate_by_name": True}


class ModelResponse(BaseModel):
    """A single pipeline's answer for one question."""
    pipeline: Pipeline
    question_id: str
    answer: str
    citations: list[str] = Field(default_factory=list)
    latency_ms: int | None = None
    notes: str | None = None
    # Illustrative cost-per-call estimate, USD. Derived from posted pricing
    # pages (TwelveLabs $0.042/min index + $0.0292/min Pegasus analyze;
    # Anthropic Haiku 4.5 input/output rates) and clearly marked as illustrative
    # — see README "Cost estimates" section.
    cost_usd: float | None = None


class JudgeScore(BaseModel):
    """Score the LLM-as-judge assigns to one model response."""
    question_id: str
    pipeline: Pipeline
    relevance: int = Field(ge=1, le=5)
    faithfulness: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    rationale: str

    @property
    def overall(self) -> float:
        return round((self.relevance + self.faithfulness + self.specificity) / 3, 2)


class QuestionResult(BaseModel):
    """Side-by-side result for a single question."""
    question: Question
    twelve_labs: ModelResponse
    clip_baseline: ModelResponse
    twelve_labs_score: JudgeScore
    clip_baseline_score: JudgeScore


class EvalReport(BaseModel):
    """Top-level eval output."""
    corpus_id: str
    n_videos: int
    n_questions: int
    results: list[QuestionResult]
    notes: list[str] = Field(default_factory=list)
    ablation: Ablation = "none"

    def rollup(self, pipeline: Pipeline) -> dict[str, float]:
        if not self.results:
            return {"relevance": 0.0, "faithfulness": 0.0, "specificity": 0.0, "overall": 0.0}
        scores = [
            r.twelve_labs_score if pipeline == "twelve_labs" else r.clip_baseline_score
            for r in self.results
        ]
        n = len(scores)
        return {
            "relevance": round(sum(s.relevance for s in scores) / n, 2),
            "faithfulness": round(sum(s.faithfulness for s in scores) / n, 2),
            "specificity": round(sum(s.specificity for s in scores) / n, 2),
            "overall": round(sum(s.overall for s in scores) / n, 2),
        }

    def rollup_by_kind(self, pipeline: Pipeline, kind: QuestionKind) -> dict[str, float]:
        relevant = [
            (r.twelve_labs_score if pipeline == "twelve_labs" else r.clip_baseline_score)
            for r in self.results
            if r.question.kind == kind
        ]
        if not relevant:
            return {"relevance": 0.0, "faithfulness": 0.0, "specificity": 0.0, "overall": 0.0, "n": 0}
        n = len(relevant)
        return {
            "relevance": round(sum(s.relevance for s in relevant) / n, 2),
            "faithfulness": round(sum(s.faithfulness for s in relevant) / n, 2),
            "specificity": round(sum(s.specificity for s in relevant) / n, 2),
            "overall": round(sum(s.overall for s in relevant) / n, 2),
            "n": n,
        }

    def cost_rollup(self, pipeline: Pipeline) -> dict[str, float]:
        responses = [
            (r.twelve_labs if pipeline == "twelve_labs" else r.clip_baseline)
            for r in self.results
        ]
        per_call = [r.cost_usd or 0.0 for r in responses]
        n = len([c for c in per_call if c > 0])
        total = sum(per_call)
        return {
            "total": round(total, 4),
            "per_question_avg": round(total / n, 4) if n else 0.0,
            "n_priced": float(n),
        }
