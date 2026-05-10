import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="SavedItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(max_length=40)),
                ("object_id", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_items", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={"unique_together": {("user", "domain", "object_id")}},
        ),
        migrations.CreateModel(
            name="UserInteraction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain", models.CharField(max_length=40)),
                ("object_id", models.PositiveIntegerField()),
                ("action", models.CharField(default="view", max_length=40)),
                ("weight", models.FloatField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interactions", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("preferred_domains", models.CharField(default="movies,music,jobs", max_length=160)),
                ("favorite_genres", models.CharField(blank=True, max_length=240)),
                ("skills", models.CharField(blank=True, max_length=500)),
                ("location", models.CharField(blank=True, max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=django.conf.settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name="userinteraction",
            index=models.Index(fields=["user", "domain", "object_id"], name="users_useri_user_id_2f1819_idx"),
        ),
    ]
