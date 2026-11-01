from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.connectors.models import PlatformAccount
from apps.hackathons.models import (
    DevpostImportRun, HackathonAchievement, HackathonEvent,
    HackathonParticipation, HackathonProject, HackathonSubmission,
)
from apps.hackathons.services.devpost.identity import external_id
from apps.hackathons.services.devpost.import_service import ImportConflict
from apps.hackathons.services.devpost.schema import normalize


ROOT = "/api/v1/hackathons/devpost/imports/"
ACCOUNTS = "/api/v1/platform-accounts/"


def sample_document(handle="example_user"):
    return {
        "format_version": 1,
        "profile_url": f"https://devpost.com/{handle}",
        "projects": [{
            "project_url": "https://devpost.com/software/smart-city-ai/",
            "title": "Smart City AI", "description": "City monitoring",
            "repository_url": "https://github.com/example/smart-city-ai",
            "technologies": ["Python", "React"],
            "submissions": [{
                "hackathon_name": "Global AI Hackathon",
                "hackathon_url": "https://global-ai-hackathon.devpost.com/",
                "status": "submitted",
            }],
        }],
    }


class DevpostImportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="devpost-owner", email="devpost-owner@example.com", password="pass12345")
        self.other = get_user_model().objects.create_user(username="devpost-other", email="devpost-other@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def link(self, reference="example_user"):
        response = self.client.post(ACCOUNTS, {"platform": "devpost", "handle": reference}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def preview(self, document=None):
        response = self.client.post(ROOT + "preview/", document or sample_document(), format="json")
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def apply(self, document, token):
        return self.client.post(ROOT, {"document": document, "preview_token": token}, format="json")

    def test_profile_link_normalization_validation_and_ownership_flag(self):
        linked = self.link("  https://devpost.com/Example_User/  ")
        self.assertEqual(linked["handle"], "example_user")
        self.assertEqual(linked["profile_url"], "https://devpost.com/example_user")
        self.assertFalse(linked["ownership_verified"])
        self.assertFalse(linked["is_verified"])
        self.assertIsNone(linked["ownership_verified_at"])
        self.assertEqual(self.client.post(ACCOUNTS, {"platform": "devpost", "handle": "another"}, format="json").status_code, 400)
        for invalid in ("", "https://devpost.com.attacker.example/user", "ftp://devpost.com/user",
                        "https://foo-.devpost.com/user",
                        "https://user:pass@devpost.com/user", "https://devpost.com/software/project", "bad name"):
            with self.subTest(invalid=invalid):
                response = self.client.patch(ACCOUNTS + f"{linked['id']}/", {"handle": invalid}, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        other_client = APIClient(); other_client.force_authenticate(self.other)
        self.assertEqual(other_client.get(ACCOUNTS).data, [])
        self.assertEqual(other_client.patch(ACCOUNTS + f"{linked['id']}/", {"handle": "other"}, format="json").status_code, 404)
        self.assertEqual(self.client.post(ACCOUNTS + f"{linked['id']}/sync/").status_code, 400)

    def test_profile_change_and_unlink_keep_historical_records(self):
        linked = self.link()
        doc = sample_document()
        token = self.preview(doc)["preview_token"]
        self.assertEqual(self.apply(doc, token).status_code, 200)
        changed = self.client.patch(ACCOUNTS + f"{linked['id']}/", {"handle": "new_user"}, format="json")
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(changed.data["profile_url"], "https://devpost.com/new_user")
        self.assertFalse(changed.data["ownership_verified"])
        self.assertEqual(self.apply(doc, token).status_code, 400)
        new_doc = sample_document("new_user")
        collision = self.preview(new_doc)
        self.assertTrue(collision["conflicts"])
        self.assertEqual(self.apply(new_doc, collision["preview_token"]).status_code, 409)
        self.assertEqual(HackathonProject.objects.count(), 1)
        self.assertEqual(self.client.delete(ACCOUNTS + f"{linked['id']}/").status_code, 204)
        self.assertEqual(HackathonProject.objects.count(), 1)
        self.assertEqual(self.client.get(ROOT).data["count"], 2)

    def test_normalization_bounds_and_stable_identities(self):
        doc = sample_document()
        normalized = normalize(doc, "example_user")
        self.assertEqual(normalized.projects[0].external_id, normalize(doc, "example_user").projects[0].external_id)
        self.assertEqual(normalized.projects[0].submissions[0].event.event_url, "https://global-ai-hackathon.devpost.com/")
        self.assertTrue(external_id("project", "example_user", normalized.projects[0].project_url).startswith("project:"))
        normalized_alias = deepcopy(doc)
        normalized_alias["projects"][0]["project_url"] = "http://www.devpost.com/software/SMART-CITY-AI"
        self.assertEqual(normalize(normalized_alias, "example_user").projects[0].external_id, normalized.projects[0].external_id)
        external_link = deepcopy(doc)
        external_link["projects"][0]["demo_url"] = "https://example.com/demo?view=full#results"
        self.assertEqual(normalize(external_link, "example_user").projects[0].demo_url, external_link["projects"][0]["demo_url"])
        for mutation in (
            lambda d: d["projects"][0].update(title=""),
            lambda d: d["projects"][0].update(project_url="https://evil.example/software/x"),
            lambda d: d["projects"][0].update(submissions=[{"hackathon_name": "A", "hackathon_url": "https://bad.example/", "status": "submitted"}]),
            lambda d: d.update(format_version=2),
            lambda d: d["projects"][0].update(owner_id=1),
            lambda d: d["projects"].append(deepcopy(d["projects"][0])),
            lambda d: d["projects"][0]["submissions"][0].update(start_date="2026-02-30"),
            lambda d: d["projects"][0]["submissions"][0].update(start_date="2026-04-03", end_date="2026-04-02"),
            lambda d: d["projects"][0]["submissions"][0].update(hackathon_url="https://foo-.devpost.com/"),
            lambda d: d["projects"][0].update(repository_url="javascript:alert(1)"),
            lambda d: d["projects"][0].update(project_url="https://devpost.com/software/smart-city-ai?ref=other"),
        ):
            with self.subTest(mutation=mutation):
                invalid = deepcopy(doc); mutation(invalid)
                with self.assertRaises(ValidationError):
                    normalize(invalid, "example_user")
        portfolio = deepcopy(doc); portfolio["projects"][0]["submissions"] = []
        self.assertEqual(normalize(portfolio, "example_user").projects[0].submissions, ())
        duplicate = deepcopy(doc)
        duplicate["projects"].append(deepcopy(doc["projects"][0]))
        duplicate["projects"][1]["project_url"] = "http://www.devpost.com/software/SMART-CITY-AI"
        with self.assertRaises(ValidationError):
            normalize(duplicate, "example_user")

    def test_preview_apply_reimport_and_overview(self):
        self.link()
        doc = sample_document()
        before = self.preview(doc)
        self.assertEqual(before["new_records"], 4)
        self.assertEqual((HackathonProject.objects.count(), HackathonEvent.objects.count(), DevpostImportRun.objects.count()), (0, 0, 0))
        applied = self.apply(doc, before["preview_token"])
        self.assertEqual(applied.status_code, 200, applied.data)
        self.assertEqual(applied.data["created_count"], 4)
        self.assertEqual((HackathonProject.objects.count(), HackathonEvent.objects.count(), HackathonParticipation.objects.count(), HackathonSubmission.objects.count()), (1, 1, 1, 1))
        self.assertEqual(HackathonParticipation.objects.get().status, "submitted")
        self.assertEqual(self.apply(doc, before["preview_token"]).data["id"], applied.data["id"])
        after = self.preview(doc)
        self.assertEqual(after["new_records"], 0)
        self.assertEqual(self.apply(doc, after["preview_token"]).status_code, 200)
        self.assertEqual((HackathonProject.objects.count(), HackathonEvent.objects.count(), HackathonSubmission.objects.count()), (1, 1, 1))
        self.assertEqual(self.client.get(ROOT).data["count"], 2)
        self.assertEqual(self.client.get(ROOT + f"{applied.data['id']}/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/hackathons/overview/").data["projects_submitted"], 1)

    def test_portfolio_only_and_multiple_submissions(self):
        self.link()
        doc = sample_document(); doc["projects"][0]["submissions"] = []
        self.assertEqual(self.apply(doc, self.preview(doc)["preview_token"]).status_code, 200)
        self.assertEqual(HackathonSubmission.objects.count(), 0)
        self.assertEqual(self.client.get("/api/v1/hackathons/overview/").data["projects_submitted"], 0)
        doc["projects"][0]["submissions"] = sample_document()["projects"][0]["submissions"] + [{
            "hackathon_name": "Second", "hackathon_url": "https://second.devpost.com/", "status": "submitted"}]
        self.assertEqual(self.apply(doc, self.preview(doc)["preview_token"]).status_code, 200)
        self.assertEqual(HackathonSubmission.objects.count(), 2)
        self.assertEqual(HackathonProject.objects.count(), 1)

    def test_manual_and_verified_context_remain_unchanged(self):
        self.link()
        manual_project = HackathonProject.objects.create(owner=self.user, title="Manual", repository_url="https://github.com/example/smart-city-ai")
        manual_event = HackathonEvent.objects.create(owner=self.user, name="Manual event", event_url="https://global-ai-hackathon.devpost.com/")
        participation = HackathonParticipation.objects.create(user=self.user, event=manual_event)
        achievement = HackathonAchievement.objects.create(participation=participation, achievement_type="placement", title="Runner-up", rank=2)
        doc = sample_document()
        before = self.preview(doc)
        self.assertEqual(before["potential_manual_duplicates"], 2)
        self.assertEqual(self.apply(doc, before["preview_token"]).status_code, 200)
        manual_project.refresh_from_db(); achievement.refresh_from_db()
        self.assertEqual(manual_project.title, "Manual")
        self.assertEqual((achievement.title, achievement.rank, achievement.verification_status), ("Runner-up", 2, "self_reported"))
        imported_event = HackathonEvent.objects.get(source="devpost")
        imported_part = HackathonParticipation.objects.get(user=self.user, event=imported_event)
        response = self.client.post("/api/v1/hackathons/achievements/", {
            "participation": imported_part.pk, "achievement_type": "award", "title": "Self-reported imported award",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["verification_status"], "self_reported")
        verified = HackathonAchievement.objects.create(participation=imported_part, submission=HackathonSubmission.objects.get(source="devpost"), achievement_type="award", title="Verified", verification_status="verified")
        changed = deepcopy(doc); changed["projects"][0]["title"] = "Changed title"
        changed["projects"][0]["submissions"][0]["hackathon_name"] = "Changed event"
        changed["projects"][0]["submissions"][0]["status"] = "withdrawn"
        plan = self.preview(changed)
        self.assertEqual(plan["protected_records"], 3)
        self.assertEqual(self.apply(changed, plan["preview_token"]).status_code, 200)
        verified.refresh_from_db()
        self.assertEqual(verified.verification_status, "verified")
        self.assertEqual(HackathonProject.objects.get(source="devpost").title, "Smart City AI")
        self.assertEqual(HackathonSubmission.objects.get(source="devpost").status, "submitted")

    def test_stale_preview_user_scope_and_invalid_payloads(self):
        self.link(); doc = sample_document(); plan = self.preview(doc)
        changed = deepcopy(doc); changed["projects"][0]["title"] = "Other"
        self.assertEqual(self.apply(changed, plan["preview_token"]).status_code, 409)
        self.assertEqual(self.client.post(ROOT, {"document": doc}, format="json").status_code, 400)
        other_client = APIClient(); other_client.force_authenticate(self.other)
        other_client.post(ACCOUNTS, {"platform": "devpost", "handle": "example_user"}, format="json")
        self.assertEqual(other_client.post(ROOT, {"document": doc, "preview_token": plan["preview_token"]}, format="json").status_code, 403)
        self.assertEqual(self.apply(doc, plan["preview_token"]).status_code, 200)
        self.assertEqual(other_client.get(ROOT).data["count"], 0)
        self.assertEqual(other_client.get(ROOT + "1/").status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(ROOT).status_code, 401)
        self.assertEqual(self.client.post(ROOT + "preview/", doc, format="json").status_code, 401)

    def test_payload_limit_and_invalid_structure(self):
        self.link()
        doc = sample_document(); doc["projects"][0]["description"] = "x" * 1_100_000
        self.assertEqual(self.client.post(ROOT + "preview/", doc, format="json").status_code, 413)
        self.assertEqual(self.client.post(ROOT + "preview/", {"format_version": 1, "profile_url": "https://devpost.com/example_user", "projects": "bad"}, format="json").status_code, 400)

    def test_imported_fields_update_and_different_users_are_isolated(self):
        self.link()
        original = sample_document()
        self.assertEqual(self.apply(original, self.preview(original)["preview_token"]).status_code, 200)
        changed = deepcopy(original)
        changed["projects"][0]["title"] = "Updated project"
        changed["projects"][0]["submissions"][0]["status"] = "withdrawn"
        plan = self.preview(changed)
        self.assertEqual(plan["new_records"], 0)
        run = self.apply(changed, plan["preview_token"])
        self.assertEqual(run.status_code, 200, run.data)
        self.assertEqual(run.data["updated_count"], 2)
        self.assertEqual(HackathonProject.objects.get(owner=self.user).title, "Updated project")
        self.assertEqual(HackathonSubmission.objects.get(owner=self.user).status, "withdrawn")
        other_client = APIClient(); other_client.force_authenticate(self.other)
        self.assertEqual(other_client.post(ACCOUNTS, {"platform": "devpost", "handle": "example_user"}, format="json").status_code, 201)
        other_plan = other_client.post(ROOT + "preview/", original, format="json")
        self.assertEqual(other_plan.status_code, 200)
        self.assertEqual(other_plan.data["new_records"], 4)
        self.assertEqual(other_client.post(ROOT, {"document": original, "preview_token": other_plan.data["preview_token"]}, format="json").status_code, 200)
        self.assertEqual(HackathonProject.objects.count(), 2)
        self.assertEqual(HackathonEvent.objects.count(), 2)

    def test_stale_and_expired_previews_leave_no_partial_records(self):
        self.link()
        doc = sample_document()
        token = self.preview(doc)["preview_token"]
        HackathonProject.objects.create(owner=self.user, source="devpost", external_id="unrelated", title="Unrelated")
        self.assertEqual(self.apply(doc, token).status_code, 200)
        new_doc = deepcopy(doc)
        new_doc["projects"][0]["project_url"] = "https://devpost.com/software/another-project"
        stale = self.preview(new_doc)["preview_token"]
        HackathonProject.objects.create(owner=self.user, source="devpost", external_id=external_id("project", "example_user", "https://devpost.com/software/another-project"), title="External change")
        response = self.apply(new_doc, stale)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(HackathonProject.objects.filter(owner=self.user).count(), 3)
        with patch("apps.hackathons.services.devpost.import_service.TOKEN_AGE", -1):
            self.assertEqual(self.apply(doc, token).status_code, 409)

    def test_database_failure_rolls_back_complete_project_graph(self):
        self.link()
        doc = sample_document()
        plan = self.preview(doc)
        with patch("apps.hackathons.services.devpost.import_service.HackathonSubmission.objects.create", side_effect=IntegrityError("private SQL detail")):
            response = self.apply(doc, plan["preview_token"])
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("private SQL detail", str(response.data))
        self.assertEqual((HackathonEvent.objects.count(), HackathonProject.objects.count(), HackathonSubmission.objects.count()), (0, 0, 0))

    def test_malformed_types_and_nonexistent_account(self):
        self.assertEqual(self.client.post(ROOT + "preview/", sample_document(), format="json").status_code, 404)
        self.link()
        for field, value in (("status", []), ("format", {})):
            with self.subTest(field=field):
                doc = sample_document()
                doc["projects"][0]["submissions"][0][field] = value
                self.assertEqual(self.client.post(ROOT + "preview/", doc, format="json").status_code, 400)
        response = self.client.generic("POST", ROOT + "preview/", b"{broken", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_history_paginates_and_remains_owner_scoped(self):
        linked = self.link()
        account = PlatformAccount.objects.get(pk=linked["id"])
        for index in range(21):
            DevpostImportRun.objects.create(
                user=self.user, linked_account=account, profile_handle=account.handle,
                status="completed", request_fingerprint=f"history-{index}",
            )
        first = self.client.get(ROOT)
        second = self.client.get(ROOT + "?page=2")
        self.assertEqual((first.status_code, first.data["count"], len(first.data["results"])), (200, 21, 20))
        self.assertEqual((second.status_code, len(second.data["results"])), (200, 1))
        other_client = APIClient(); other_client.force_authenticate(self.other)
        self.assertEqual(other_client.get(ROOT).data["count"], 0)

    def test_account_unlink_during_apply_records_controlled_failure(self):
        linked = self.link()
        document = sample_document()
        token = self.preview(document)["preview_token"]

        def unlink_before_persistence(*_args):
            PlatformAccount.objects.filter(pk=linked["id"]).delete()
            raise ImportConflict("Linked Devpost account changed. Preview again.")

        with patch("apps.hackathons.devpost_views.apply_import", side_effect=unlink_before_persistence):
            response = self.apply(document, token)
        self.assertEqual(response.status_code, 409)
        run = DevpostImportRun.objects.get()
        self.assertEqual(run.status, "failed")
        self.assertIsNone(run.linked_account_id)
        self.assertEqual(HackathonProject.objects.count(), 0)
