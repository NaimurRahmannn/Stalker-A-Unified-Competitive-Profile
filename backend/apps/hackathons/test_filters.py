from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.hackathons.models import HackathonEvent, HackathonParticipation, HackathonProject, HackathonSubmission


class DiscoveryFilterTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="discoverer", email="discoverer@example.com", password="pass12345")
        self.other = user_model.objects.create_user(username="other-discoverer", email="other-discoverer@example.com", password="pass12345")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)
        self.alpha = HackathonProject.objects.create(owner=self.owner, title="Alpha tool", description="Useful Python project",
            technologies=["Python", "React"], is_public=True)
        self.beta = HackathonProject.objects.create(owner=self.owner, title="Beta tool", description="Data science work",
            technologies=["Pythonista", "Rust"], source="devpost", external_id="beta", is_public=False)
        self.gamma = HackathonProject.objects.create(owner=self.owner, title="Gamma", description="Uses python for data",
            technologies=["PYTHON"], is_public=False)
        HackathonProject.objects.create(owner=self.other, title="Other Python", technologies=["Python"], is_public=True)
        self.old_event = HackathonEvent.objects.create(owner=self.owner, name="Old Summit", start_date=date(2024, 6, 1), format="online")
        self.new_event = HackathonEvent.objects.create(owner=self.owner, name="New Summit", start_date=date(2026, 6, 1), format="hybrid",
            source="devpost", external_id="new")
        self.undated = HackathonEvent.objects.create(owner=self.owner, name="Undated meetup")
        HackathonEvent.objects.create(owner=self.other, name="Other Summit", start_date=date(2026, 6, 1))
        HackathonParticipation.objects.create(user=self.owner, event=self.old_event, status="attended")
        HackathonParticipation.objects.create(user=self.owner, event=self.new_event, status="submitted")
        HackathonSubmission.objects.create(owner=self.owner, project=self.alpha, event=self.old_event, status="submitted")
        HackathonSubmission.objects.create(owner=self.owner, project=self.alpha, event=self.new_event, status="submitted")

    def projects(self, query=""):
        return self.client.get("/api/v1/hackathons/projects/" + query)

    def events(self, query=""):
        return self.client.get("/api/v1/hackathons/events/" + query)

    def test_search_combined_filters_and_related_count(self):
        response = self.projects("?search=PYTHON&source=manual&visibility=public&technology=python")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.alpha.pk])
        self.assertEqual(response.data["results"][0]["related_hackathon_count"], 2)
        self.assertEqual([row["id"] for row in self.projects("?title=beta").data["results"]], [self.beta.pk])
        self.assertEqual([row["id"] for row in self.projects("?search=DATA").data["results"]], [self.gamma.pk, self.beta.pk])
        self.assertEqual([row["id"] for row in self.projects("?technology=python").data["results"]], [self.gamma.pk, self.alpha.pk])
        self.assertEqual(self.projects("?search=missing").data["count"], 0)

    def test_project_validation_ordering_and_pagination(self):
        for query in ("?source=other", "?visibility=hidden", "?ordering=title;drop", "?search=" + "x" * 101,
                      "?technology=" + "x" * 101):
            with self.subTest(query=query):
                self.assertEqual(self.projects(query).status_code, 400)
        self.assertEqual([row["id"] for row in self.projects("?ordering=title_asc&page_size=2").data["results"]],
                         [self.alpha.pk, self.beta.pk])
        self.assertEqual([row["id"] for row in self.projects("?ordering=title_asc&page_size=2&page=2").data["results"]],
                         [self.gamma.pk])
        self.assertEqual([row["id"] for row in self.projects("?ordering=oldest").data["results"]],
                         [self.alpha.pk, self.beta.pk, self.gamma.pk])
        self.assertEqual([row["id"] for row in self.projects("?ordering=title_desc").data["results"]],
                         [self.gamma.pk, self.beta.pk, self.alpha.pk])
        tied = timezone.now() + timedelta(days=1)
        HackathonProject.objects.filter(pk__in=[self.alpha.pk, self.beta.pk]).update(created_at=tied)
        self.assertEqual([row["id"] for row in self.projects("?ordering=newest").data["results"]],
                         [self.beta.pk, self.alpha.pk, self.gamma.pk])

    def test_event_filters_and_missing_dates_last(self):
        response = self.events("?name=summit&status=submitted&year=2026&event_format=hybrid&source=devpost")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.new_event.pk])
        self.assertEqual([row["id"] for row in self.events("?ordering=date_newest").data["results"]],
                         [self.new_event.pk, self.old_event.pk, self.undated.pk])
        self.assertEqual([row["id"] for row in self.events("?ordering=date_oldest").data["results"]],
                         [self.old_event.pk, self.new_event.pk, self.undated.pk])
        self.assertEqual([row["id"] for row in self.events("?ordering=name_asc&page_size=2").data["results"]],
                         [self.new_event.pk, self.old_event.pk])
        for query in ("?status=invalid", "?event_format=virtual", "?source=other", "?ordering=unsafe", "?year=abc", "?year=12345"):
            with self.subTest(query=query):
                self.assertEqual(self.events(query).status_code, 400)
        self.assertEqual(self.events("?name=not-found").data["count"], 0)

    def test_authentication_and_owner_scope(self):
        self.assertEqual(self.projects().data["count"], 3)
        self.assertEqual(self.events().data["count"], 3)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.projects().data["count"], 1)
        self.assertEqual(self.events().data["count"], 1)
        self.assertEqual(self.client.get(f"/api/v1/hackathons/projects/{self.alpha.pk}/").status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.projects().status_code, 401)
