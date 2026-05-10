from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    preferred_domains = models.CharField(max_length=160, default="movies,music,jobs")
    favorite_genres = models.CharField(max_length=240, blank=True)
    skills = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} profile"


class UserInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interactions")
    domain = models.CharField(max_length=40)
    object_id = models.PositiveIntegerField()
    action = models.CharField(max_length=40, default="view")
    weight = models.FloatField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "domain", "object_id"])]
        ordering = ["-created_at"]


class SavedItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_items")
    domain = models.CharField(max_length=40)
    object_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "domain", "object_id")
