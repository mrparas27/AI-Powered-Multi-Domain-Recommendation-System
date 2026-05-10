from django.contrib import admin
from apps.recommendations.models import RecommendationEvent


@admin.register(RecommendationEvent)
class RecommendationEventAdmin(admin.ModelAdmin):
    list_display = ("domain", "query", "result_count", "user", "created_at")
    list_filter = ("domain", "created_at")
    search_fields = ("query", "explanation")
