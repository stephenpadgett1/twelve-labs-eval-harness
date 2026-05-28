"""Render an EvalReport as a markdown side-by-side report."""

from __future__ import annotations

from .types import EvalReport, ModelResponse, Pipeline, QuestionResult


def render(report: EvalReport) -> str:
    lines: list[str] = []

    lines.append("# Video-Understanding Eval — Side-by-Side Report")
    lines.append("")
    lines.append(
        f"Corpus: **{report.corpus_id}** · "
        f"{report.n_videos} videos · {report.n_questions} questions"
    )
    lines.append("")

    if report.notes:
        lines.append("> **Run notes:**")
        for n in report.notes:
            lines.append(f"> - {n}")
        lines.append("")

    lines.append("## Rollup")
    lines.append("")
    lines.append("| Metric | Twelve Labs (Marengo + Pegasus) | CLIP baseline + Claude reasoning |")
    lines.append("|---|---:|---:|")
    tl = report.rollup("twelve_labs")
    cb = report.rollup("clip_baseline")
    for key in ("relevance", "faithfulness", "specificity", "overall"):
        lines.append(f"| {key.capitalize()} | {tl[key]:.2f} | {cb[key]:.2f} |")
    lines.append("")

    lines.append("### By question kind")
    lines.append("")
    lines.append("| Kind | Pipeline | n | Relevance | Faithfulness | Specificity | Overall |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for kind in ("retrieval", "reasoning"):
        tl_k = report.rollup_by_kind("twelve_labs", kind)  # type: ignore[arg-type]
        cb_k = report.rollup_by_kind("clip_baseline", kind)  # type: ignore[arg-type]
        lines.append(
            f"| {kind} | Twelve Labs | {tl_k['n']} | {tl_k['relevance']:.2f} | "
            f"{tl_k['faithfulness']:.2f} | {tl_k['specificity']:.2f} | {tl_k['overall']:.2f} |"
        )
        lines.append(
            f"| {kind} | CLIP baseline | {cb_k['n']} | {cb_k['relevance']:.2f} | "
            f"{cb_k['faithfulness']:.2f} | {cb_k['specificity']:.2f} | {cb_k['overall']:.2f} |"
        )
    lines.append("")

    lines.append("## Per-question detail")
    lines.append("")
    for r in report.results:
        lines.append(f"### {r.question.id} · {r.question.video_id} · _{r.question.kind}_")
        lines.append("")
        lines.append(f"**Q.** {r.question.prompt}")
        lines.append("")
        lines.append(f"**Expected.** {r.question.expects}")
        lines.append("")
        lines.append(_response_block("Twelve Labs", r.twelve_labs, r.twelve_labs_score.relevance, r.twelve_labs_score.faithfulness, r.twelve_labs_score.specificity, r.twelve_labs_score.rationale))
        lines.append("")
        lines.append(_response_block("CLIP baseline", r.clip_baseline, r.clip_baseline_score.relevance, r.clip_baseline_score.faithfulness, r.clip_baseline_score.specificity, r.clip_baseline_score.rationale))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _response_block(
    label: str,
    response: ModelResponse,
    relevance: int,
    faithfulness: int,
    specificity: int,
    rationale: str,
) -> str:
    latency = f" · {response.latency_ms} ms" if response.latency_ms else ""
    notes = f"\n_notes: {response.notes}_" if response.notes else ""
    return (
        f"**{label}** (relevance {relevance}/5 · faithfulness {faithfulness}/5 · "
        f"specificity {specificity}/5{latency})\n\n"
        f"{response.answer}\n\n"
        f"_judge:_ {rationale}{notes}"
    )
