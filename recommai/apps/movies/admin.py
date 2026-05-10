from django.contrib import admin
from apps.movies.models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_year", "genres", "rating", "popularity")
    search_fields = ("title", "overview", "genres", "cast", "director")
    list_filter = ("release_year", "genres")
