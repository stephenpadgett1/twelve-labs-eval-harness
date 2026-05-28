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

    assert len(report.results) == 24
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
    tl_str = report.rollup_by_kind("twelve_labs", "structured")
    assert tl_ret["n"] + tl_rea["n"] + tl_str["n"] == len(questions)


def test_structured_pegasus_15_outperforms_baseline_on_structured_kind():
    """The whole point of Time-Based Metadata: video-native temporal boundaries
    beat frame-sampled Claude's coarse-bucket guesses on schema-conformant
    extraction."""
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
    )
    tl = report.rollup_by_kind("twelve_labs", "structured")
    cb = report.rollup_by_kind("clip_baseline", "structured")
    assert tl["n"] >= 4
    assert tl["overall"] > cb["overall"]
    # Pegasus 1.5 TBM should be near-perfect on these illustrative fixtures.
    assert tl["overall"] >= 4.5


def test_cost_rollup_attaches_estimates_to_every_response():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    report = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
    )
    tl_cost = report.cost_rollup("twelve_labs")
    cb_cost = report.cost_rollup("clip_baseline")
    assert tl_cost["total"] > 0
    assert cb_cost["total"] > 0
    # Every TL response should carry a non-zero illustrative cost.
    assert all(r.twelve_labs.cost_usd and r.twelve_labs.cost_usd > 0 for r in report.results)


def test_visual_only_ablation_degrades_audio_heavy_lecture_questions():
    """The whole point of the audio ablation: lecture (speech-heavy) questions
    should score lower in visual-only mode; sports/product questions shouldn't
    change meaningfully."""
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)

    full = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(audio_enabled=True),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
        ablation="none",
    )
    visual = run_eval(
        videos=videos,
        questions=questions,
        twelve_labs=TwelveLabsClient(audio_enabled=False),
        clip_baseline=ClipBaselineClient(),
        judge=Judge(),
        ablation="visual_only",
    )

    full_tl = full.rollup("twelve_labs")
    vis_tl = visual.rollup("twelve_labs")
    assert vis_tl["overall"] < full_tl["overall"], (
        "audio ablation should reduce TL overall score on this corpus"
    )

    # And the degradation should concentrate on retrieval (where audio
    # carries the speech signal in the lecture videos).
    full_ret = full.rollup_by_kind("twelve_labs", "retrieval")
    vis_ret = visual.rollup_by_kind("twelve_labs", "retrieval")
    assert vis_ret["overall"] < full_ret["overall"]
