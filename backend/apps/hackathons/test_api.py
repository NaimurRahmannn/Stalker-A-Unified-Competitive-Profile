"""Phase 2 API integration and isolation tests."""

from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from apps.hackathons.admin import HackathonAchievementAdmin, HackathonEventAdmin
from apps.hackathons.models import (
    HackathonAchievement, HackathonEvent, HackathonParticipation,
    HackathonProject, HackathonSubmission,
)


ROOT = "/api/v1/hackathons/"


class ManualAPITests(APITestCase):
    def setUp(self):
        user = get_user_model()
        self.alice = user.objects.create_user(username="api-alice", email="api-a@example.com", password="test12345")
        self.bob = user.objects.create_user(username="api-bob", email="api-b@example.com", password="test12345")
        self.client.force_authenticate(self.alice)
        self.event = HackathonEvent.objects.create(owner=self.alice, name="Alpha")
        self.other_event = HackathonEvent.objects.create(owner=self.bob, name="Private")
        self.project = HackathonProject.objects.create(owner=self.alice, title="Tool")
        self.other_project = HackathonProject.objects.create(owner=self.bob, title="Secret")
        self.participation = HackathonParticipation.objects.create(user=self.alice, event=self.event, status="attended")
        self.other_participation = HackathonParticipation.objects.create(user=self.bob, event=self.other_event)
        self.submission = HackathonSubmission.objects.create(owner=self.alice, event=self.event, project=self.project, status="submitted")
        self.other_submission = HackathonSubmission.objects.create(owner=self.bob, event=self.other_event, project=self.other_project)
        self.achievement = HackathonAchievement.objects.create(participation=self.participation, achievement_type="award", title="Best AI")
        self.other_achievement = HackathonAchievement.objects.create(participation=self.other_participation, achievement_type="award", title="Secret Award")

    def test_authentication_for_every_resource_action(self):
        self.client.force_authenticate(user=None)
        for resource in ("events", "projects", "participations", "submissions", "achievements"):
            self.assertEqual(self.client.get(ROOT + resource + "/").status_code, 401)
            self.assertEqual(self.client.post(ROOT + resource + "/", {}).status_code, 401)
            self.assertEqual(self.client.patch(ROOT + resource + "/1/", {}).status_code, 401)
            self.assertEqual(self.client.delete(ROOT + resource + "/1/").status_code, 401)
        self.assertEqual(self.client.post(ROOT + "entries/", {}).status_code, 401)

    def test_user_scoped_paginated_lists_and_private_details(self):
        resources = {"events": self.other_event, "projects": self.other_project,
                     "participations": self.other_participation, "submissions": self.other_submission,
                     "achievements": self.other_achievement}
        for resource, other in resources.items():
            url = ROOT + resource + "/"
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("results", response.data)
            self.assertEqual(response.data["count"], 1)
            self.assertEqual(self.client.get(f"{url}{other.pk}/").status_code, 404)
            self.assertEqual(self.client.patch(f"{url}{other.pk}/", {"title": "Changed"}).status_code, 404)
            self.assertEqual(self.client.delete(f"{url}{other.pk}/").status_code, 404)

    def test_event_list_prefetches_related_records(self):
        for index in range(5):
            event = HackathonEvent.objects.create(owner=self.alice, name=f"Event {index}")
            participation = HackathonParticipation.objects.create(user=self.alice, event=event)
            HackathonAchievement.objects.create(participation=participation, achievement_type="award", title="Prize")
            HackathonSubmission.objects.create(owner=self.alice, event=event, project=self.project)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(ROOT + "events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 6)
        self.assertLessEqual(len(queries), 7)

    def test_crud_and_protected_fields(self):
        cases = [
            ("events", {"name": "New"}, {"organizer": "Group"}),
            ("projects", {"title": "New"}, {"description": "Text"}),
            ("participations", {"event": HackathonEvent.objects.create(owner=self.alice, name="Second").pk}, {"team_name": "Team"}),
            ("submissions", {"event": HackathonEvent.objects.create(owner=self.alice, name="Third").pk, "project": self.project.pk}, {"status": "submitted"}),
            ("achievements", {"participation": self.participation.pk, "achievement_type": "finalist", "title": "Global Finalist"}, {"description": "Final round"}),
        ]
        for resource, payload, change in cases:
            url = ROOT + resource + "/"
            response = self.client.post(url, payload, format="json")
            self.assertEqual(response.status_code, 201, response.data)
            detail = f"{url}{response.data['id']}/"
            self.assertEqual(self.client.get(detail).status_code, 200)
            self.assertEqual(self.client.patch(detail, change, format="json").status_code, 200)
            self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertEqual(self.client.post(ROOT + "events/", {"name": "Bad", "owner": self.bob.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "events/", {"name": "Bad", "source": "devpost"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "projects/", {"title": "Bad", "external_id": "fake"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "achievement_type": "award", "title": "Bad", "verification_status": "verified"}, format="json").status_code, 400)

    def test_relationships_duplicates_and_validation(self):
        self.assertEqual(self.client.post(ROOT + "submissions/", {"event": self.event.pk, "project": self.other_project.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "participations/", {"event": self.other_event.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "participations/", {"event": self.event.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "submissions/", {"event": self.event.pk, "project": self.project.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "submission": self.other_submission.pk, "achievement_type": "award", "title": "Bad"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(ROOT + f"submissions/{self.submission.pk}/", {"event": self.other_event.pk}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(ROOT + f"achievements/{self.achievement.pk}/", {"participation": self.other_participation.pk}, format="json").status_code, 400)
        for rank in (0, -1, 3):
            response = self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "achievement_type": "placement", "title": "Place", "rank": rank, "total_participants": 2}, format="json")
            self.assertEqual(response.status_code, 400, response.data)
        response = self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "achievement_type": "award", "title": "Custom award", "evidence_url": "bad"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "achievement_type": "finalist", "title": "Global Finalist"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data["rank"])
        self.assertEqual(response.data["verification_status"], "self_reported")

    def test_composite_cases_and_rollback(self):
        base = {"event": {"name": "Hack A"}, "participation": {"status": "registered"}}
        response = self.client.post(ROOT + "entries/", base, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data["project_id"])
        self.assertEqual(self.client.get(ROOT + "overview/").data["hackathons_attended"], 1)
        with_project = {"event": {"name": "Hack B"}, "participation": {"status": "submitted"}, "project_id": self.project.pk, "submission": {"status": "submitted"}, "achievements": [{"achievement_type": "placement", "title": "Runner up", "rank": 2, "total_participants": 10, "link_submission": True}, {"achievement_type": "award", "title": "Best AI"}]}
        response = self.client.post(ROOT + "entries/", with_project, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["achievement_ids"]), 2)
        self.assertEqual(self.client.get(ROOT + "overview/").data["projects_submitted"], 1)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event_id": response.data["event_id"], "participation": {}, "achievements": [{"achievement_type": "finalist", "title": "Finalist"}]}, format="json").status_code, 201)
        self.assertEqual(HackathonParticipation.objects.filter(event_id=response.data["event_id"]).count(), 1)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event": {"name": "With award"}, "participation": {"status": "attended"}, "achievements": [{"achievement_type": "award", "title": "People's Choice"}]}, format="json").status_code, 201)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event": {"name": "With new project"}, "participation": {"status": "submitted"}, "project": {"title": "New tool"}, "submission": {"status": "submitted"}}, format="json").status_code, 201)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event_id": self.event.pk, "participation": {"status": "attended"}, "project": {"title": "Another tool"}, "submission": {"status": "draft"}}, format="json").status_code, 201)
        counts = (HackathonEvent.objects.count(), HackathonProject.objects.count(), HackathonAchievement.objects.count())
        bad = {"event": {"name": "Orphan"}, "participation": {}, "project": {"title": "Orphan project"}, "submission": {}, "achievements": [{"achievement_type": "award", "title": "Award", "link_submission": True}, {"achievement_type": "placement", "title": "Wrong", "rank": 3, "total_participants": 2}]}
        self.assertEqual(self.client.post(ROOT + "entries/", bad, format="json").status_code, 400)
        self.assertEqual((HackathonEvent.objects.count(), HackathonProject.objects.count(), HackathonAchievement.objects.count()), counts)
        late_bad = {"event": {"name": "Late orphan"}, "participation": {}, "achievements": [{"achievement_type": "award", "title": "Award", "link_submission": True}]}
        self.assertEqual(self.client.post(ROOT + "entries/", late_bad, format="json").status_code, 400)
        self.assertEqual((HackathonEvent.objects.count(), HackathonProject.objects.count(), HackathonAchievement.objects.count()), counts)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event_id": self.other_event.pk, "participation": {}}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event": {"name": "Bad"}, "participation": {}, "project_id": self.other_project.pk, "submission": {}}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event": {"name": "Bad"}, "participation": {"user": self.bob.pk}}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "entries/", {"event": {"name": "Bad"}, "participation": {}, "achievements": [{"achievement_type": "award", "title": "Bad", "verification_status": "verified"}]}, format="json").status_code, 400)

    def test_imported_core_records_are_read_only(self):
        imported = HackathonEvent.objects.create(owner=self.alice, name="Imported", source="devpost", external_id="dp1")
        self.assertEqual(self.client.patch(ROOT + f"events/{imported.pk}/", {"name": "Wrong"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(ROOT + f"events/{imported.pk}/").status_code, 403)
        # The existing project/event pair already has a manual submission, so use a second project.
        imported_project = HackathonProject.objects.create(owner=self.alice, title="Imported project", source="devpost", external_id="dp-proj")
        imported_submission = HackathonSubmission.objects.create(owner=self.alice, event=self.event, project=imported_project, source="devpost", external_id="dp-sub")
        self.assertEqual(self.client.delete(ROOT + f"events/{self.event.pk}/").status_code, 403)
        self.assertEqual(self.client.delete(ROOT + f"projects/{imported_project.pk}/").status_code, 403)
        self.assertTrue(HackathonSubmission.objects.filter(pk=imported_submission.pk).exists())

    def test_verified_achievement_is_read_only_but_self_reported_is_editable(self):
        url = ROOT + f"achievements/{self.achievement.pk}/"
        self.assertEqual(self.client.patch(url, {"title": "Updated award"}, format="json").status_code, 200)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.title, "Updated award")
        self.achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
        self.achievement.save()
        for method, payload in (
            ("patch", {"title": "Forged title"}),
            ("patch", {"rank": 1}),
            ("patch", {"achievement_type": "placement"}),
            ("patch", {"evidence_url": "https://example.com/fake"}),
            ("put", {"achievement_type": "placement", "title": "Forged title", "rank": 1}),
        ):
            with self.subTest(method=method, payload=payload):
                response = getattr(self.client, method)(url, payload, format="json")
                self.assertEqual(response.status_code, 403, response.data)
                self.achievement.refresh_from_db()
                self.assertEqual(self.achievement.title, "Updated award")
                self.assertIsNone(self.achievement.rank)
                self.assertEqual(self.achievement.achievement_type, "award")
                self.assertEqual(self.achievement.evidence_url, "")
                self.assertEqual(self.achievement.verification_status, "verified")
        self.assertEqual(self.client.patch(url, {"verification_status": "verified"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        other_url = ROOT + f"achievements/{self.other_achievement.pk}/"
        self.assertEqual(self.client.patch(other_url, {"title": "Hidden"}, format="json").status_code, 404)

    def test_admin_can_still_verify_achievement(self):
        admin_user = get_user_model().objects.create_superuser(username="review-admin", email="admin@example.com", password="test12345")
        request = RequestFactory().get("/admin/")
        request.user = admin_user
        admin = HackathonAchievementAdmin(HackathonAchievement, AdminSite())
        self.assertNotIn("verification_status", admin.get_readonly_fields(request, self.achievement))
        self.client.force_authenticate(user=None)
        self.client.force_login(admin_user)
        response = self.client.post(
            f"/admin/hackathons/hackathonachievement/{self.achievement.pk}/change/",
            {
                "achievement_type": "award", "title": self.achievement.title,
                "rank": "", "total_participants": "", "description": "",
                "evidence_url": "", "submission": "",
                "verification_status": "verified", "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302, response.context)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.verification_status, "verified")

    def test_related_deletes_cannot_remove_or_unlink_verified_achievement(self):
        self.achievement.submission = self.submission
        self.achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
        self.achievement.save()
        for resource, record in (
            ("events", self.event),
            ("projects", self.project),
            ("participations", self.participation),
            ("submissions", self.submission),
            ("achievements", self.achievement),
        ):
            with self.subTest(resource=resource):
                response = self.client.delete(ROOT + f"{resource}/{record.pk}/")
                self.assertEqual(response.status_code, 403, response.data)
                self.achievement.refresh_from_db()
                self.assertEqual(self.achievement.verification_status, "verified")
                self.assertEqual(self.achievement.submission_id, self.submission.pk)

    def test_self_reported_context_and_unrelated_records_remain_editable(self):
        cases = (
            ("events", self.event, {"name": "Renamed local hackathon"}),
            ("participations", self.participation, {"team_name": "New team"}),
            ("submissions", self.submission, {"status": "draft"}),
            ("projects", self.project, {"title": "Renamed project"}),
        )
        for resource, record, payload in cases:
            with self.subTest(resource=resource):
                response = self.client.patch(ROOT + f"{resource}/{record.pk}/", payload, format="json")
                self.assertEqual(response.status_code, 200, response.data)
                record.refresh_from_db()
                for field, value in payload.items():
                    self.assertEqual(getattr(record, field), value)

        self.achievement.submission = self.submission
        self.achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
        self.achievement.save()
        other_event = HackathonEvent.objects.create(owner=self.alice, name="Unrelated event")
        other_project = HackathonProject.objects.create(owner=self.alice, title="Unrelated project")
        other_submission = HackathonSubmission.objects.create(owner=self.alice, event=other_event, project=other_project)
        self.assertEqual(self.client.patch(ROOT + f"projects/{other_project.pk}/", {"title": "Still editable"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(ROOT + f"submissions/{other_submission.pk}/", {"status": "submitted"}, format="json").status_code, 200)

    def test_verified_context_is_read_only_for_user_updates(self):
        self.achievement.submission = self.submission
        self.achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
        self.achievement.save()
        overview_before = self.client.get(ROOT + "overview/").data
        cases = (
            ("events", self.event, {"name": "Major Global Hackathon"}),
            ("events", self.event, {"organizer": "Famous Organizer"}),
            ("events", self.event, {"event_url": "https://example.com/major"}),
            ("participations", self.participation, {"team_name": "Winning team"}),
            ("participations", self.participation, {"status": "submitted"}),
            ("submissions", self.submission, {"status": "withdrawn"}),
            ("submissions", self.submission, {"submission_url": "https://example.com/other"}),
            ("projects", self.project, {"title": "Other project"}),
            ("projects", self.project, {"repository_url": "https://example.com/other"}),
            ("achievements", self.achievement, {"title": "First Place"}),
        )
        for resource, record, payload in cases:
            with self.subTest(resource=resource, payload=payload):
                before = {field: getattr(record, field) for field in payload}
                response = self.client.patch(ROOT + f"{resource}/{record.pk}/", payload, format="json")
                self.assertEqual(response.status_code, 403, response.data)
                record.refresh_from_db()
                for field, value in before.items():
                    self.assertEqual(getattr(record, field), value)
                self.assertEqual(self.achievement.verification_status, "verified")
        self.assertEqual(self.client.put(ROOT + f"events/{self.event.pk}/", {"name": "Other"}, format="json").status_code, 403)
        self.assertEqual(self.client.get(ROOT + "overview/").data, overview_before)
        self.assertEqual(self.client.patch(ROOT + f"events/{self.other_event.pk}/", {"name": "Guess"}, format="json").status_code, 404)
        self.assertEqual(self.client.patch(ROOT + f"projects/{self.other_project.pk}/", {"title": "Guess"}, format="json").status_code, 404)

    def test_admin_can_correct_verified_event_context(self):
        self.achievement.verification_status = HackathonAchievement.VerificationStatus.VERIFIED
        self.achievement.save()
        admin_user = get_user_model().objects.create_superuser(username="context-admin", email="context-admin@example.com", password="test12345")
        request = RequestFactory().get("/admin/")
        request.user = admin_user
        admin = HackathonEventAdmin(HackathonEvent, AdminSite())
        self.assertNotIn("name", admin.get_readonly_fields(request, self.event))
        self.client.force_authenticate(user=None)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(f"/admin/hackathons/hackathonevent/{self.event.pk}/change/").status_code, 302)
        self.client.force_login(admin_user)
        response = self.client.post(
            f"/admin/hackathons/hackathonevent/{self.event.pk}/change/",
            {
                "name": "Corrected event", "organizer": "Corrected organizer",
                "description": "", "event_url": "", "start_date": "", "end_date": "",
                "format": "unknown", "source": "manual", "external_id": "", "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302, response.context)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Corrected event")

    def test_owner_scoped_event_name_search_is_paginated(self):
        for index in range(25):
            HackathonEvent.objects.create(owner=self.alice, name=f"Long running hack {index}")
        HackathonEvent.objects.create(owner=self.bob, name="Long running hack private")
        first = self.client.get(ROOT + "events/?name=running&page=1")
        second = self.client.get(ROOT + "events/?name=running&page=2")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["count"], 25)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertEqual(len(second.data["results"]), 5)
        self.assertTrue(all("running" in item["name"] for item in first.data["results"] + second.data["results"]))
        self.assertEqual(self.client.get(ROOT + "events/?name=private").data["count"], 0)

    def test_http_only_url_fields_in_crud_and_composite(self):
        cases = (
            ("events", self.event.pk, "event_url"),
            ("projects", self.project.pk, "repository_url"),
            ("projects", self.project.pk, "demo_url"),
            ("projects", self.project.pk, "video_url"),
            ("projects", self.project.pk, "image_url"),
            ("submissions", self.submission.pk, "submission_url"),
            ("achievements", self.achievement.pk, "evidence_url"),
        )
        for resource, record_id, field in cases:
            url = ROOT + f"{resource}/{record_id}/"
            for value in ("https://example.com", "http://example.com", ""):
                with self.subTest(resource=resource, field=field, value=value):
                    self.assertEqual(self.client.patch(url, {field: value}, format="json").status_code, 200)
            for value in ("ftp://example.com", "javascript:alert(1)", "file:///etc/passwd"):
                with self.subTest(resource=resource, field=field, value=value):
                    response = self.client.patch(url, {field: value}, format="json")
                    self.assertEqual(response.status_code, 400, response.data)
                    self.assertIn(field, response.data)
        self.assertEqual(self.client.post(ROOT + "events/", {"name": "New", "event_url": "ftp://example.com"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "projects/", {"title": "New", "repository_url": "ftp://example.com"}, format="json").status_code, 400)
        new_event = HackathonEvent.objects.create(owner=self.alice, name="New submission")
        self.assertEqual(self.client.post(ROOT + "submissions/", {"event": new_event.pk, "project": self.project.pk, "submission_url": "ftp://example.com"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(ROOT + "achievements/", {"participation": self.participation.pk, "achievement_type": "award", "title": "New", "evidence_url": "ftp://example.com"}, format="json").status_code, 400)
        composite_cases = (
            {"event": {"name": "Bad", "event_url": "ftp://example.com"}, "participation": {}},
            {"event": {"name": "Bad"}, "participation": {}, "project": {"title": "Bad", "demo_url": "ftp://example.com"}, "submission": {}},
            {"event": {"name": "Bad"}, "participation": {}, "project_id": self.project.pk, "submission": {"submission_url": "ftp://example.com"}},
            {"event": {"name": "Bad"}, "participation": {}, "achievements": [{"achievement_type": "award", "title": "Bad", "evidence_url": "ftp://example.com"}]},
        )
        for payload in composite_cases:
            response = self.client.post(ROOT + "entries/", payload, format="json")
            self.assertEqual(response.status_code, 400, response.data)
