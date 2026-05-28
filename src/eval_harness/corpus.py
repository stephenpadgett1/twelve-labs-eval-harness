"""Corpus + question loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from .types import Question, Video


def load_videos(path: Path) -> list[Video]:
    raw = yaml.safe_load(path.read_text())
    return [Video.model_validate(v) for v in raw["videos"]]


def load_questions(path: Path, videos: list[Video]) -> list[Question]:
    raw = yaml.safe_load(path.read_text())
    by_video: dict[str, list[dict]] = raw["questions"]
    video_ids = {v.id for v in videos}

    out: list[Question] = []
    for video_id, qs in by_video.items():
        if video_id not in video_ids:
            raise ValueError(f"question set references unknown video: {video_id}")
        for q in qs:
            out.append(Question.model_validate({**q, "video_id": video_id}))
    return out
