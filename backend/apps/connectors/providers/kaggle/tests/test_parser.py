import json
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.connectors.providers.kaggle.exceptions import KaggleDocumentError
from apps.connectors.providers.kaggle.normalizer import normalize_profile
from apps.connectors.providers.kaggle.parser import parse_profile_document


FIXTURE = Path(__file__).parent / "fixtures" / "complete_profile.html"


def document(tracks=None, *, username="example_user", observed_at="2026-11-01T12:00:00Z"):
    payload = {"username": username, "observed_at": observed_at, "tracks": tracks if tracks is not None else {}}
    return '<html><script type="application/json" data-stalker-kaggle-profile="v1">' + json.dumps(payload) + '</script></html>'


class KaggleParserTests(SimpleTestCase):
    def test_complete_synthetic_profile(self):
        normalized = normalize_profile(parse_profile_document(FIXTURE.read_text(), "example_user"))
        by_track = {row.track: row for row in normalized.tracks}
        self.assertEqual(set(by_track), {"competitions", "code", "datasets"})
        self.assertEqual(by_track["competitions"].values["global_rank"], 1234)
        self.assertEqual(by_track["competitions"].values["tier"], "Expert")
        self.assertEqual(by_track["competitions"].values["silver_medals"], 0)
        self.assertIsNone(by_track["datasets"].values["silver_medals"])

    def test_grandmaster_and_partial_profiles(self):
        data = normalize_profile(parse_profile_document(document({
            "competitions": {"global_rank": "42", "tier": "gRaNdMaStEr"},
            "code": {"rank_status": "unranked"},
            "datasets": {"rank_status": "unknown"},
        }), "EXAMPLE_USER"))
        self.assertEqual(data.tracks[0].values["tier"], "Grandmaster")
        self.assertEqual(data.tracks[1].rank_status, "unranked")
        self.assertEqual(data.tracks[2].rank_status, "unknown")
        self.assertEqual(normalize_profile(parse_profile_document(document(), "example_user")).tracks, ())

    def test_missing_values_are_not_fabricated(self):
        data = normalize_profile(parse_profile_document(document({
            "competitions": {"tier": "Expert"},
        }), "example_user"))
        self.assertNotIn("global_rank", data.tracks[0].values)
        self.assertNotIn("gold_medals", data.tracks[0].values)
        self.assertEqual(data.tracks[0].rank_status, "unknown")

    def test_ranked_requires_a_global_rank(self):
        with self.assertRaises(KaggleDocumentError) as raised:
            normalize_profile(parse_profile_document(document({
                "competitions": {"rank_status": "ranked", "tier": "Expert"},
            }), "example_user"))
        self.assertEqual(raised.exception.code, "invalid_rank_status")

    def test_duplicate_fields_and_missing_identity_fail_without_network(self):
        duplicate = ('<html><script type="application/json" data-stalker-kaggle-profile="v1">'
                     '{"username":"example_user","username":"other","observed_at":"2026-11-01T12:00:00Z","tracks":{}}'
                     '</script></html>')
        missing = document().replace('"username": "example_user", ', "")
        with patch("requests.get", side_effect=AssertionError("network access")):
            for source, code in ((duplicate, "duplicate_field"), (missing, "unsupported_schema")):
                with self.subTest(code=code), self.assertRaises(KaggleDocumentError) as raised:
                    parse_profile_document(source, "example_user")
                self.assertEqual(raised.exception.code, code)

    def test_invalid_identity_and_markup_fail_with_codes(self):
        for source, code in (
            (document(username="someone_else"), "identity_mismatch"),
            ("<html>unrelated</html>", "unsupported_markup"),
            ("not HTML", "unsupported_markup"),
            ('<html><script type="application/json" data-stalker-kaggle-profile="v1">{bad}</script></html>', "invalid_document"),
            (document(observed_at="yesterday"), "invalid_timestamp"),
            (document({"private": {"global_rank": 1}}), "invalid_track"),
        ):
            with self.subTest(code=code), self.assertRaises(KaggleDocumentError) as raised:
                normalize_profile(parse_profile_document(source, "example_user"))
            self.assertEqual(raised.exception.code, code)

    def test_invalid_ranks_points_tiers_and_status_are_rejected(self):
        for field, value in (
            ("global_rank", 0), ("global_rank", "1,2"), ("highest_rank", -1),
            ("gold_medals", -1), ("silver_medals", 2**40),
            ("points", "NaN"), ("points", "1,2"), ("points", "1.12345"),
            ("tier", "Legend"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(KaggleDocumentError):
                normalize_profile(parse_profile_document(document({"code": {field: value}}), "example_user"))
        with self.assertRaises(KaggleDocumentError):
            normalize_profile(parse_profile_document(document({"code": {"rank_status": "unranked", "global_rank": 5}}), "example_user"))
