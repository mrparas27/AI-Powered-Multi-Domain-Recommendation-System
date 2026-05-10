import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=240, unique=True)),
                ("website", models.URLField(blank=True)),
                ("logo_url", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("location", models.CharField(blank=True, max_length=180)),
            ],
            options={"verbose_name_plural": "companies", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_id", models.CharField(blank=True, max_length=160, null=True, unique=True)),
                ("title", models.CharField(max_length=240)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("description", models.TextField(blank=True)),
                ("requirements", models.TextField(blank=True)),
                ("skills", models.CharField(blank=True, max_length=500)),
                ("salary_min", models.PositiveIntegerField(blank=True, null=True)),
                ("salary_max", models.PositiveIntegerField(blank=True, null=True)),
                ("job_type", models.CharField(blank=True, max_length=80)),
                ("apply_url", models.URLField(blank=True)),
                ("posted_at", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="jobs", to="jobs.company")),
            ],
            options={"ordering": ["-posted_at", "title"]},
        ),
    ]
