from datetime import datetime, timezone as datetime_timezone
from typing import Any

from apps.connectors.base.exceptions import ProviderSchemaError


def _schema_error(index: int, field: str) -> ProviderSchemaError:
    return ProviderSchemaError(
        f"AtCoderProblems submission {index} has an invalid {field} field."
    )


def _required_int(value: Any, index: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _schema_error(index, field)
    return value


def _optional_int(value: Any, index: int, field: str) -> int | None:
    if value is None:
        return None
    return _required_int(value, index, field)


def _required_text(value: Any, index: int, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _schema_error(index, field)
    return value.strip()


def _optional_text(value: Any, index: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _schema_error(index, field)
    value = value.strip()
    return value or None


def normalize_atcoder_submissions(
    raw_submissions: list[dict[str, Any]],
    expected_handle: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for index, submission in enumerate(raw_submissions):
        if not isinstance(submission, dict):
            raise ProviderSchemaError(
                f"AtCoderProblems submission {index} is not an object."
            )

        user_id = _required_text(submission.get("user_id"), index, "user_id")
        if user_id.casefold() != expected_handle.casefold():
            raise ProviderSchemaError(
                f"AtCoderProblems submission {index} belongs to a different user."
            )

        submission_id = _required_int(submission.get("id"), index, "id")
        epoch_second = _required_int(
            submission.get("epoch_second"), index, "epoch_second"
        )
        code_size = _optional_int(submission.get("length"), index, "length")
        execution_time = _optional_int(
            submission.get("execution_time"), index, "execution_time"
        )
        if submission_id < 0 or epoch_second < 0:
            raise _schema_error(index, "id/epoch_second")
        if code_size is not None and code_size < 0:
            raise _schema_error(index, "length")
        if execution_time is not None and execution_time < 0:
            raise _schema_error(index, "execution_time")

        point = submission.get("point")
        if point is not None and (
            isinstance(point, bool) or not isinstance(point, (int, float))
        ):
            raise _schema_error(index, "point")

        normalized.append(
            {
                "external_submission_id": submission_id,
                "external_contest_id": _required_text(
                    submission.get("contest_id"), index, "contest_id"
                ),
                "external_problem_id": _required_text(
                    submission.get("problem_id"), index, "problem_id"
                ),
                "verdict": _required_text(
                    submission.get("result"), index, "result"
                ),
                "language": _optional_text(
                    submission.get("language"), index, "language"
                ),
                "submitted_at": datetime.fromtimestamp(
                    epoch_second,
                    tz=datetime_timezone.utc,
                ),
                "provider_epoch_second": epoch_second,
                "execution_time_ms": execution_time,
                "code_size_bytes": code_size,
                "metadata": ({"score": point} if point is not None else {}),
            }
        )

    normalized.sort(
        key=lambda item: (
            item["provider_epoch_second"],
            item["external_submission_id"],
        )
    )
    return normalized
