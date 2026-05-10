from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=240, unique=True)
    website = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=180, blank=True)

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Job(models.Model):
    job_id = models.CharField(max_length=160, unique=True, null=True, blank=True)
    title = models.CharField(max_length=240)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    skills = models.CharField(max_length=500, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    job_type = models.CharField(max_length=80, blank=True)
    apply_url = models.URLField(blank=True)
    posted_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-posted_at", "title"]

    def __str__(self):
        company_name = self.company.name if self.company else "Unknown Company"
        return f"{self.title} at {company_name}"

    @property
    def recommendation_text(self):
        company_name = self.company.name if self.company else ""
        return " ".join([self.title, company_name, self.location, self.description, self.requirements, self.skills])
