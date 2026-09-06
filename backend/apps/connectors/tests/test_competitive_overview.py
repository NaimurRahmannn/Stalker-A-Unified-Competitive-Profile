from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    CodeforcesStats,
    LeetCodeStats,
    PlatformAccount,
)

User = get_user_model()


class CompetitiveProgrammingOverviewTests(APITestCase):
    url = "/api/v1/competitive-programming/overview/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="overview-user",
            email="overview@example.com",
            password="StrongPassword123!",
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_platforms_returns_zero_summary_and_connectable_platforms(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["active_platforms"], 0)
        self.assertEqual(response.data["summary"]["solved_count"], 0)
        self.assertTrue(response.data["summary"]["solved_count_complete"])
        self.assertEqual(
            [item["platform"] for item in response.data["platforms"]],
            ["codeforces", "atcoder", "leetcode"],
        )
        self.assertTrue(
            all(not item["connected"] for item in response.data["platforms"])
        )
        self.assertEqual(response.data["recent_activity"], [])

    def test_combines_metrics_propagates_completeness_and_orders_activity(self):
        now = timezone.now()
        codeforces = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="cf-user",
        )
        CodeforcesStats.objects.create(
            platform_account=codeforces,
            handle="cf-user",
            rating=1700,
            max_rating=1800,
            rank="expert",
            solved_count=100,
            attempted_count=120,
            accepted_submission_count=130,
            contest_count=20,
            recent_activity=[
                {
                    "submission_id": 10,
                    "contest_id": 1,
                    "problem_index": "A",
                    "problem_name": "Array Test",
                    "problem_rating": 800,
                    "verdict": "OK",
                    "language": "GNU C++20",
                    "submitted_at": (now - timedelta(hours=2)).isoformat(),
                }
            ],
        )
        atcoder = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="ac-user",
        )
        AtCoderStats.objects.create(
            platform_account=atcoder,
            current_rating=1500,
            max_rating=1600,
            rated_contest_count=30,
            solved_count=50,
            attempted_count=70,
            accepted_submission_count=80,
            indexed_submission_count=100,
            submission_backfill_complete=False,
        )
        AtCoderSubmission.objects.create(
            platform_account=atcoder,
            external_submission_id=99,
            external_contest_id="abc350",
            external_problem_id="abc350_a",
            verdict="AC",
            language="C++ 23",
            submitted_at=now - timedelta(hours=1),
            provider_epoch_second=int((now - timedelta(hours=1)).timestamp()),
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        summary = response.data["summary"]
        self.assertEqual(summary["active_platforms"], 2)
        self.assertEqual(summary["solved_count"], 150)
        self.assertFalse(summary["solved_count_complete"])
        self.assertEqual(summary["contest_count"], 50)
        self.assertEqual(summary["accepted_submission_count"], 210)
        self.assertFalse(summary["accepted_submission_count_complete"])
        atcoder_summary = response.data["platforms"][1]
        self.assertEqual(atcoder_summary["rank"], "cyan")
        self.assertFalse(atcoder_summary["solved_count_complete"])
        self.assertEqual(
            [item["platform"] for item in response.data["recent_activity"]],
            ["atcoder", "codeforces"],
        )
        self.assertEqual(response.data["recent_activity"][0]["title"], "abc350_a")

    def test_atcoder_only_complete_totals_and_activity_are_bounded(self):
        now = timezone.now()
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="complete-user",
        )
        AtCoderStats.objects.create(
            platform_account=account,
            solved_count=25,
            attempted_count=30,
            accepted_submission_count=40,
            indexed_submission_count=45,
            submission_backfill_complete=True,
        )
        AtCoderSubmission.objects.bulk_create(
            [
                AtCoderSubmission(
                    platform_account=account,
                    external_submission_id=index + 1,
                    external_contest_id="abc999",
                    external_problem_id=f"abc999_{index}",
                    verdict="AC",
                    submitted_at=now - timedelta(minutes=index),
                    provider_epoch_second=int(
                        (now - timedelta(minutes=index)).timestamp()
                    ),
                )
                for index in range(25)
            ]
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        summary = response.data["summary"]
        self.assertEqual(summary["active_platforms"], 1)
        self.assertEqual(summary["solved_count"], 25)
        self.assertTrue(summary["solved_count_complete"])
        self.assertEqual(len(response.data["recent_activity"]), 20)
        self.assertEqual(response.data["recent_activity"][0]["id"], "atcoder-1")

    def test_leetcode_contributes_only_comparable_unified_metrics(self):
        codeforces = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="cf-user",
        )
        CodeforcesStats.objects.create(
            platform_account=codeforces,
            handle="cf-user",
            solved_count=100,
            accepted_submission_count=120,
            contest_count=20,
        )
        leetcode = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="lc-user",
        )
        LeetCodeStats.objects.create(
            platform_account=leetcode,
            solved_total=80,
            solved_easy=40,
            solved_medium=30,
            solved_hard=10,
            problem_stats_complete=True,
            current_contest_rating=1842.75,
            attended_contest_count=12,
            data_updated_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        summary = response.data["summary"]
        self.assertEqual(summary["active_platforms"], 2)
        self.assertEqual(summary["solved_count"], 180)
        self.assertTrue(summary["solved_count_complete"])
        self.assertEqual(summary["contest_count"], 32)
        self.assertEqual(summary["accepted_submission_count"], 120)
        self.assertFalse(summary["accepted_submission_count_complete"])
        leetcode_summary = response.data["platforms"][2]
        self.assertEqual(leetcode_summary["rating"], 1842.75)
        self.assertEqual(
            leetcode_summary["problem_breakdown"],
            {"easy": 40, "medium": 30, "hard": 10},
        )

    def test_leetcode_only_incomplete_stats_propagate_completeness(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="lc-only",
        )
        LeetCodeStats.objects.create(
            platform_account=account,
            solved_total=40,
            problem_stats_complete=False,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.data["summary"]["active_platforms"], 1)
        self.assertEqual(response.data["summary"]["solved_count"], 40)
        self.assertFalse(response.data["summary"]["solved_count_complete"])
