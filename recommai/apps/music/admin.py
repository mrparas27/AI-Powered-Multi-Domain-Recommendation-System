from django.contrib import admin
from apps.music.models import Artist, Song


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "genres", "popularity", "followers")
    search_fields = ("name", "genres")


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "album", "popularity", "energy", "danceability")
    search_fields = ("title", "album", "artist__name", "genres", "mood")
    list_filter = ("genres", "mood")
