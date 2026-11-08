from django.test import SimpleTestCase

from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity


class KaggleIdentityTests(SimpleTestCase):
    def test_username_and_canonical_url(self):
        identity = normalize_kaggle_identity("  Example_User ")
        self.assertEqual(identity.username, "Example_User")
        self.assertEqual(identity.lookup_key, "example_user")
        self.assertEqual(identity.profile_url, "https://www.kaggle.com/Example_User")
        self.assertEqual(
            normalize_kaggle_identity("https://www.kaggle.com/Example_User").lookup_key,
            identity.lookup_key,
        )

    def test_rejects_unsafe_and_unsupported_references(self):
        for value in (
            "", "   ", "a b", "a.b", "../admin", "a\n", "http://www.kaggle.com/user",
            "https://evil.com/user", "https://kaggle.com.evil.com/user",
            "https://user:pass@www.kaggle.com/user", "https://www.kaggle.com/user/account",
            "https://www.kaggle.com/user?x=1", "https://www.kaggle.com/user#tab",
            "https://www.kaggle.com/user?", "https://www.kaggle.com/user#",
            "https://www.kaggle.com/user/", "https://www.kaggle.com/%2e%2e",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_kaggle_identity(value)
