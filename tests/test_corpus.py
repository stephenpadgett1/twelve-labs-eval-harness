from pathlib import Path

import pytest

from eval_harness.corpus import load_questions, load_videos

ROOT = Path(__file__).resolve().parents[1]


def test_loads_six_videos():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    assert len(videos) == 6
    assert {v.use_case for v in videos} == {"product_demo", "sports_action", "lecture"}


def test_loads_full_question_set_referencing_real_videos():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    assert len(questions) == 24
    video_ids = {v.id for v in videos}
    assert all(q.video_id in video_ids for q in questions)


def test_question_kinds_include_retrieval_reasoning_structured():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    kinds = {q.kind for q in questions}
    assert kinds == {"retrieval", "reasoning", "structured"}
    n_retrieval = sum(1 for q in questions if q.kind == "retrieval")
    n_reasoning = sum(1 for q in questions if q.kind == "reasoning")
    n_structured = sum(1 for q in questions if q.kind == "structured")
    assert n_retrieval >= 8
    assert n_reasoning >= 4
    assert n_structured >= 4


def test_structured_questions_carry_a_schema():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    for q in questions:
        if q.kind == "structured":
            assert q.schema_ is not None, f"{q.id} is structured but has no schema"
            assert q.schema_.get("type") == "object"


def test_unknown_video_id_in_questions_raises(tmp_path: Path):
    bad = tmp_path / "questions.yaml"
    bad.write_text("questions:\n  VID-DOES-NOT-EXIST:\n    - {id: Q-X, kind: retrieval, prompt: x, expects: y}\n")
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    with pytest.raises(ValueError, match="unknown video"):
        load_questions(bad, videos)
