import json
from pathlib import Path


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "evals"
    / "golden-cases"
    / "password-reset-001.json"
)


def test_password_reset_golden_case_contains_expected_topics():
    case = json.loads(FIXTURE.read_text(encoding="utf-8-sig"))

    transcript = case["transcript"].lower()
    expected_topics = case["expected"]["required_topics"]

    for topic in expected_topics:
        assert topic.lower() in transcript, (
            f"Golden case transcript is missing expected topic: {topic}"
        )
