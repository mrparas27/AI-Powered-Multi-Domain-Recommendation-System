from django.conf import settings
from django.db import models


class RecommendationEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    domain = models.CharField(max_length=40)
    query = models.CharField(max_length=300, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.domain}: {self.result_count} results"
