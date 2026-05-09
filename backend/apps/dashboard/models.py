from django.db import models
from django.utils import timezone


class ProfileSnapshot(models.Model):
	external_account = models.ForeignKey(
		"accounts.ExternalAccount",
		on_delete=models.CASCADE,
		related_name="snapshots",
	)
	captured_at = models.DateTimeField(default=timezone.now)
	display_name = models.CharField(max_length=255, null=True, blank=True)
	headline_rank_title = models.CharField(max_length=120, null=True, blank=True)
	rating = models.IntegerField(null=True, blank=True)
	highest_rating = models.IntegerField(null=True, blank=True)
	contests_count = models.IntegerField(null=True, blank=True)
	solved_count = models.IntegerField(null=True, blank=True)
	avatar_url = models.URLField(max_length=500, null=True, blank=True)
	metadata_json = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-captured_at", "-id"]

	def __str__(self) -> str:
		return f"snapshot::{self.external_account.source}::{self.external_account.handle_or_slug}"
