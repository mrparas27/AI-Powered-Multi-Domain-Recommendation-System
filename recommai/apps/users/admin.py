from django.contrib import admin
from apps.users.models import SavedItem, UserInteraction, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_domains", "location", "updated_at")
    search_fields = ("user__username", "favorite_genres", "skills", "location")


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "domain", "object_id", "action", "weight", "created_at")
    list_filter = ("domain", "action")


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ("user", "domain", "object_id", "created_at")
    list_filter = ("domain",)
