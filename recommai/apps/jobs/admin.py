from django.contrib import admin
from apps.jobs.models import Company, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "website")
    search_fields = ("name", "description", "location")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "job_type", "salary_min", "salary_max", "posted_at")
    search_fields = ("title", "description", "requirements", "skills", "company__name")
    list_filter = ("job_type", "location", "posted_at")
