from datetime import datetime, timezone as datetime_timezone

from django.test import SimpleTestCase

from apps.connectors.base.exceptions import ProviderSchemaError
from apps.connectors.providers.atcoder.problems_mapper import (
    normalize_atcoder_submissions,
)


def raw_submission(
    submission_id: int = 100,
    epoch_second: int = 1700000000,
    *,
    problem_id: str = "abc100_a",
    contest_id: str = "abc100",
    result: str = "AC",
    language: str | None = "C++ 20 (gcc 12.2)",
) -> dict:
    return {
        "id": submission_id,
        "epoch_second": epoch_second,
        "problem_id": problem_id,
        "contest_id": contest_id,
        "user_id": "AtCoder_User",
        "language": language,
        "point": 100.0,
        "length": 512,
        "result": result,
        "execution_time": 24,
    }


class AtCoderProblemsMapperTests(SimpleTestCase):
    def test_normalizes_submission_fields_and_timestamp(self):
        submission = normalize_atcoder_submissions(
            [raw_submission()],
            expected_handle="atcoder_user",
        )[0]

        self.assertEqual(submission["external_submission_id"], 100)
        self.assertEqual(submission["external_problem_id"], "abc100_a")
        self.assertEqual(submission["external_contest_id"], "abc100")
        self.assertEqual(submission["verdict"], "AC")
        self.assertEqual(submission["language"], "C++ 20 (gcc 12.2)")
        self.assertEqual(submission["execution_time_ms"], 24)
        self.assertEqual(submission["code_size_bytes"], 512)
        self.assertEqual(submission["metadata"], {"score": 100.0})
        self.assertEqual(
            submission["submitted_at"],
            datetime.fromtimestamp(1700000000, tz=datetime_timezone.utc),
        )

    def test_unknown_verdict_is_preserved(self):
        submission = normalize_atcoder_submissions(
            [raw_submission(result="WJ")],
            expected_handle="atcoder_user",
        )[0]

        self.assertEqual(submission["verdict"], "WJ")

    def test_optional_fields_can_be_null(self):
        raw = raw_submission(language=None)
        raw["execution_time"] = None
        raw["length"] = None
        raw["point"] = None

        submission = normalize_atcoder_submissions(
            [raw],
            expected_handle="atcoder_user",
        )[0]

        self.assertIsNone(submission["language"])
        self.assertIsNone(submission["execution_time_ms"])
        self.assertIsNone(submission["code_size_bytes"])
        self.assertEqual(submission["metadata"], {})

    def test_results_are_sorted_by_epoch_then_submission_id(self):
        normalized = normalize_atcoder_submissions(
            [
                raw_submission(3, 101),
                raw_submission(2, 100),
                raw_submission(1, 100),
            ],
            expected_handle="atcoder_user",
        )

        self.assertEqual(
            [item["external_submission_id"] for item in normalized],
            [1, 2, 3],
        )

    def test_different_user_is_rejected(self):
        raw = raw_submission()
        raw["user_id"] = "someone_else"

        with self.assertRaisesRegex(ProviderSchemaError, "different user"):
            normalize_atcoder_submissions([raw], expected_handle="atcoder_user")

    def test_missing_or_malformed_required_fields_are_rejected(self):
        required_fields = (
            "id",
            "epoch_second",
            "problem_id",
            "contest_id",
            "user_id",
            "result",
        )
        for field in required_fields:
            with self.subTest(field=field):
                raw = raw_submission()
                raw.pop(field)
                with self.assertRaises(ProviderSchemaError):
                    normalize_atcoder_submissions(
                        [raw],
                        expected_handle="atcoder_user",
                    )
