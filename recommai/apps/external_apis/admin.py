from django.contrib import admin
from apps.external_apis.models import APICache, APIRequestLog, ImportLog


@admin.register(APICache)
class APICacheAdmin(admin.ModelAdmin):
    list_display = ("provider", "key", "expires_at", "updated_at")
    list_filter = ("provider", "expires_at")
    search_fields = ("key",)


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ("provider", "endpoint", "status_code", "success", "latency_ms", "created_at")
    list_filter = ("provider", "success", "created_at")
    search_fields = ("endpoint", "error")


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("provider", "domain", "query", "imported_count", "created_at")
    list_filter = ("provider", "domain", "created_at")
