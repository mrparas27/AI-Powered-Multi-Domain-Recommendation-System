from django.db import models


class Movie(models.Model):
    tmdb_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    title = models.CharField(max_length=240)
    overview = models.TextField(blank=True)
    genres = models.CharField(max_length=240, blank=True)
    cast = models.CharField(max_length=500, blank=True)
    director = models.CharField(max_length=180, blank=True)
    release_year = models.PositiveIntegerField(null=True, blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True)
    rating = models.FloatField(default=0)
    popularity = models.FloatField(default=0)
    poster_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-popularity", "-rating", "title"]

    def __str__(self):
        return self.title

    @property
    def recommendation_text(self):
        return " ".join([self.title, self.overview, self.genres, self.cast, self.director])
