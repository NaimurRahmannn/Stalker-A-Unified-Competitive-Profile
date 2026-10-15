from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("connectors", "0009_ctfteamprofile_ctftimesyncstate_ctfyearlyranking"),
    ]

    operations = [
        migrations.AddField(
            model_name="ctfyearlyranking",
            name="organizer_points",
            field=models.FloatField(default=0.0),
        ),
    ]
