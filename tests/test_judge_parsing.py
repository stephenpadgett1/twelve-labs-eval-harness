import pytest

from eval_harness.clients.judge import Judge


@pytest.mark.parametrize(
    "text",
    [
        '{"relevance": 5, "faithfulness": 4, "specificity": 3, "rationale": "ok"}',
        'Sure! Here you go:\n```json\n{"relevance": 5, "faithfulness": 4, "specificity": 3, "rationale": "ok"}\n```',
        'Some preamble\n{"relevance": 5, "faithfulness": 4, "specificity": 3, "rationale": "ok"}\ntrailing',
    ],
)
def test_parse_json_extracts_object_under_wrappers(text):
    parsed = Judge._parse_json(text)
    assert parsed == {
        "relevance": 5,
        "faithfulness": 4,
        "specificity": 3,
        "rationale": "ok",
    }


def test_parse_json_raises_on_non_json():
    with pytest.raises(ValueError, match="non-JSON"):
        Judge._parse_json("this is just prose")
