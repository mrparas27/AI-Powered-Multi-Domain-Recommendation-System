from django.db import models
from django.utils import timezone


class APICache(models.Model):
    key = models.CharField(max_length=320, unique=True)
    provider = models.CharField(max_length=80)
    payload = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["provider", "expires_at"])]
        ordering = ["-updated_at"]

    @property
    def is_fresh(self):
        return self.expires_at > timezone.now()


class APIRequestLog(models.Model):
    provider = models.CharField(max_length=80)
    endpoint = models.CharField(max_length=260)
    status_code = models.PositiveIntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ImportLog(models.Model):
    provider = models.CharField(max_length=80)
    domain = models.CharField(max_length=40)
    query = models.CharField(max_length=240, blank=True)
    imported_count = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
