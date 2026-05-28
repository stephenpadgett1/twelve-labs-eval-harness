"""Eval orchestration. Runs both pipelines over the corpus, scores with the
judge, returns a populated EvalReport."""

from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .clients.clip_baseline import ClipBaselineClient
from .clients.judge import Judge
from .clients.twelve_labs import TwelveLabsClient
from .types import Ablation, EvalReport, ModelResponse, Question, QuestionResult, Video

console = Console()


def run_eval(
    *,
    videos: list[Video],
    questions: list[Question],
    twelve_labs: TwelveLabsClient,
    clip_baseline: ClipBaselineClient,
    judge: Judge,
    corpus_id: str = "demo",
    ablation: Ablation = "none",
) -> EvalReport:
    videos_by_id = {v.id: v for v in videos}
    results: list[QuestionResult] = []

    console.print(
        f"[bold]Running eval[/]: {len(questions)} questions across {len(videos)} videos"
    )
    console.print(
        f"  twelve_labs: [cyan]{twelve_labs.mode}[/]  "
        f"clip_baseline: [cyan]{clip_baseline.mode}[/]  "
        f"judge: [cyan]{judge.mode}[/]  "
        f"ablation: [cyan]{ablation}[/]"
    )

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task_id = progress.add_task("evaluating...", total=len(questions))

        for question in questions:
            video = videos_by_id[question.video_id]
            progress.update(task_id, description=f"{question.id} ({question.kind}) · {video.id}")

            tl_response = _twelve_labs_for(question, video, twelve_labs)
            cb_response = _baseline_for(question, video, clip_baseline)

            tl_score = judge.score(question, tl_response)
            cb_score = judge.score(question, cb_response)

            results.append(
                QuestionResult(
                    question=question,
                    twelve_labs=tl_response,
                    clip_baseline=cb_response,
                    twelve_labs_score=tl_score,
                    clip_baseline_score=cb_score,
                )
            )
            progress.advance(task_id)

    report = EvalReport(
        corpus_id=corpus_id,
        n_videos=len(videos),
        n_questions=len(questions),
        results=results,
        notes=_run_notes(twelve_labs, clip_baseline, judge, ablation),
        ablation=ablation,
    )
    return report


def _twelve_labs_for(
    question: Question, video: Video, client: TwelveLabsClient
) -> ModelResponse:
    if question.kind == "retrieval":
        return client.search(video, question)
    if question.kind == "structured":
        return client.extract_structured(video, question)
    return client.generate(video, question)


def _baseline_for(
    question: Question, video: Video, client: ClipBaselineClient
) -> ModelResponse:
    if question.kind == "retrieval":
        return client.retrieve(video, question)
    if question.kind == "structured":
        return client.extract_structured(video, question)
    return client.reason(video, question)


def _run_notes(
    twelve_labs: TwelveLabsClient,
    clip_baseline: ClipBaselineClient,
    judge: Judge,
    ablation: Ablation,
) -> list[str]:
    notes: list[str] = []
    if twelve_labs.mode == "fixtures":
        notes.append(
            "twelve_labs ran in fixture mode (no TWELVE_LABS_API_KEY set). "
            "Responses are pre-recorded illustrative shapes, not live model output."
        )
    if clip_baseline.mode == "fixtures":
        notes.append(
            "clip_baseline ran in fixture mode (no ANTHROPIC_API_KEY for the multimodal call). "
            "Responses are pre-recorded illustrative shapes."
        )
    if judge.mode == "fixtures":
        notes.append(
            "judge ran in fixture mode (no ANTHROPIC_API_KEY). "
            "Scores are pre-recorded against the fixture responses, not live judge calls."
        )
    if ablation == "visual_only":
        notes.append(
            "Audio modality ablation active: Marengo runs visual-only. "
            "Run the default mode (no --ablation flag) to see the audio delta — "
            "the speech-heavy lectures degrade most."
        )
    return notes
