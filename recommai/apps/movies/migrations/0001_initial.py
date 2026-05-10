from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Movie",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tmdb_id", models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ("title", models.CharField(max_length=240)),
                ("overview", models.TextField(blank=True)),
                ("genres", models.CharField(blank=True, max_length=240)),
                ("cast", models.CharField(blank=True, max_length=500)),
                ("director", models.CharField(blank=True, max_length=180)),
                ("release_year", models.PositiveIntegerField(blank=True, null=True)),
                ("runtime", models.PositiveIntegerField(blank=True, null=True)),
                ("rating", models.FloatField(default=0)),
                ("popularity", models.FloatField(default=0)),
                ("poster_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-popularity", "-rating", "title"]},
        ),
    ]
