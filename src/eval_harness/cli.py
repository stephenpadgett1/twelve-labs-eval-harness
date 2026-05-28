"""CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import click

from .clients.clip_baseline import ClipBaselineClient
from .clients.judge import Judge
from .clients.twelve_labs import TwelveLabsClient
from .corpus import load_questions, load_videos
from .report import render
from .runner import run_eval
from .types import Ablation

ROOT = Path(__file__).resolve().parents[2]


@click.command()
@click.option(
    "--videos-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=ROOT / "corpus" / "videos.yaml",
    show_default=True,
)
@click.option(
    "--questions-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=ROOT / "questions" / "questions.yaml",
    show_default=True,
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=ROOT / "output" / "eval-report.md",
    show_default=True,
)
@click.option("--corpus-id", default="demo", show_default=True)
@click.option(
    "--ablation",
    type=click.Choice(["none", "visual_only"]),
    default="none",
    show_default=True,
    help="Modality ablation. visual_only disables audio for Marengo so you can "
    "measure the audio delta on speech-heavy queries.",
)
def main(
    videos_file: Path,
    questions_file: Path,
    output: Path,
    corpus_id: str,
    ablation: str,
) -> None:
    """Run the eval and write a side-by-side markdown report."""
    videos = load_videos(videos_file)
    questions = load_questions(questions_file, videos)

    audio_enabled = ablation == "none"
    twelve_labs = TwelveLabsClient(audio_enabled=audio_enabled)
    clip_baseline = ClipBaselineClient()
    judge = Judge()

    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=twelve_labs,
        clip_baseline=clip_baseline,
        judge=judge,
        corpus_id=corpus_id,
        ablation=ablation,  # type: ignore[arg-type]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(report))
    click.echo(f"Wrote report → {output}")


if __name__ == "__main__":
    main()
