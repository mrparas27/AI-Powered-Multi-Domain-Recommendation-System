import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Artist",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("spotify_id", models.CharField(blank=True, max_length=120, null=True, unique=True)),
                ("name", models.CharField(max_length=240)),
                ("genres", models.CharField(blank=True, max_length=300)),
                ("popularity", models.PositiveIntegerField(default=0)),
                ("image_url", models.URLField(blank=True)),
                ("followers", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("spotify_id", models.CharField(blank=True, max_length=120, null=True, unique=True)),
                ("title", models.CharField(max_length=240)),
                ("album", models.CharField(blank=True, max_length=240)),
                ("genres", models.CharField(blank=True, max_length=300)),
                ("mood", models.CharField(blank=True, max_length=80)),
                ("duration_ms", models.PositiveIntegerField(default=0)),
                ("popularity", models.PositiveIntegerField(default=0)),
                ("tempo", models.FloatField(default=0)),
                ("energy", models.FloatField(default=0)),
                ("danceability", models.FloatField(default=0)),
                ("valence", models.FloatField(default=0)),
                ("acousticness", models.FloatField(default=0)),
                ("preview_url", models.URLField(blank=True)),
                ("image_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("artist", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="songs", to="music.artist")),
            ],
            options={"ordering": ["-popularity", "title"]},
        ),
    ]
