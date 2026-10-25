from django.conf import settings
from django.db import migrations, models


def backfill_submission_owners(apps, schema_editor):
    HackathonSubmission = apps.get_model("hackathons", "HackathonSubmission")
    for sub in HackathonSubmission.objects.filter(owner__isnull=True).select_related("event"):
        sub.owner_id = sub.event.owner_id
        sub.save(update_fields=["owner"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("hackathons", "0002_add_hackathon_integrity_constraints"),
    ]

    operations = [
        # Step 1: Add owner as nullable so existing records do not fail
        migrations.AddField(
            model_name="hackathonsubmission",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=models.CASCADE,
                related_name="hackathon_submissions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Step 2: Backfill owner from the associated event.owner
        migrations.RunPython(
            backfill_submission_owners,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 3: Enforce null=False now that all records have an owner
        migrations.AlterField(
            model_name="hackathonsubmission",
            name="owner",
            field=models.ForeignKey(
                null=False,
                on_delete=models.CASCADE,
                related_name="hackathon_submissions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Step 4: Remove the old per-event unique constraint
        migrations.RemoveConstraint(
            model_name="hackathonsubmission",
            name="unique_hack_sub_event_ext_id",
        ),
        # Step 5: Add the user-scoped (owner, source, external_id) unique constraint
        migrations.AddConstraint(
            model_name="hackathonsubmission",
            constraint=models.UniqueConstraint(
                condition=models.Q(("external_id", ""), _negated=True),
                fields=("owner", "source", "external_id"),
                name="unique_hack_sub_owner_ext_id",
            ),
        ),
        # Step 6: Add owner-based indexes for query efficiency
        migrations.AddIndex(
            model_name="hackathonsubmission",
            index=models.Index(
                fields=["owner", "-created_at"],
                name="hack_sub_owner_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hackathonsubmission",
            index=models.Index(
                fields=["owner", "source", "external_id"],
                name="hack_sub_owner_ext_idx",
            ),
        ),
    ]
