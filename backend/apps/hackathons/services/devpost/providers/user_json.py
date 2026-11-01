"""The only enabled Phase 3 acquisition adapter."""

from rest_framework.exceptions import ValidationError


class UserJsonProvider:
    input_method = "user_json"

    def acquire(self, supplied) -> dict:
        if not isinstance(supplied, dict):
            raise ValidationError({"document": "Provide a JSON object."})
        return supplied
