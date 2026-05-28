from pathlib import Path

import pytest

from eval_harness.corpus import load_questions, load_videos

ROOT = Path(__file__).resolve().parents[1]


def test_loads_six_videos():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    assert len(videos) == 6
    assert {v.use_case for v in videos} == {"product_demo", "sports_action", "lecture"}


def test_loads_twenty_questions_referencing_real_videos():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    assert len(questions) == 20
    video_ids = {v.id for v in videos}
    assert all(q.video_id in video_ids for q in questions)


def test_question_kinds_mix_retrieval_and_reasoning():
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    questions = load_questions(ROOT / "questions" / "questions.yaml", videos)
    kinds = {q.kind for q in questions}
    assert kinds == {"retrieval", "reasoning"}
    # Reasonable balance — neither kind should be < 1/4 of the set.
    n_retrieval = sum(1 for q in questions if q.kind == "retrieval")
    assert 5 <= n_retrieval <= 15


def test_unknown_video_id_in_questions_raises(tmp_path: Path):
    bad = tmp_path / "questions.yaml"
    bad.write_text("questions:\n  VID-DOES-NOT-EXIST:\n    - {id: Q-X, kind: retrieval, prompt: x, expects: y}\n")
    videos = load_videos(ROOT / "corpus" / "videos.yaml")
    with pytest.raises(ValueError, match="unknown video"):
        load_questions(bad, videos)
