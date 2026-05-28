"""End-to-end smoke test against the committed fixtures."""

from pathlib import Path

from eval_harness.clients.clip_baseline import ClipBaselineClient
from eval_harness.clients.judge import Judge
from eval_harness.clients.twelve_labs import TwelveLabsClient
from eval_harness.corpus import load_questions, load_videos
from eval_harness.report import render
from eval_harness.runner import run_eval

ROOT = Path(__file__).resolve().parents[1]


def test_full_eval_against_fixtures():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)

    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
        corpus_id="test",
    )

    assert len(report.results) == 20
    # Twelve Labs should outperform the CLIP baseline overall on the demo fixtures
    # (the gap is the whole point of the example). Asserts the rollup math works.
    tl = report.rollup("twelve_labs")
    cb = report.rollup("clip_baseline")
    assert tl["overall"] > cb["overall"]
    assert 4.0 < tl["overall"] <= 5.0
    assert 2.0 < cb["overall"] < 4.5


def test_report_renders_with_per_question_detail():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
    )
    markdown = render(report)
    assert "## Rollup" in markdown
    assert "### By question kind" in markdown
    # Every question id appears at least once in the detail section.
    for q in questions:
        assert q.id in markdown


def test_rollup_by_kind_partitions_questions():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
    )

    tl_ret = report.rollup_by_kind("twelve_labs", "retrieval")
    tl_rea = report.rollup_by_kind("twelve_labs", "reasoning")
    assert tl_ret["n"] + tl_rea["n"] == len(questions)
