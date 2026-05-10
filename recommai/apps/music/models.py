from django.db import models


class Artist(models.Model):
    spotify_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    name = models.CharField(max_length=240)
    genres = models.CharField(max_length=300, blank=True)
    popularity = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    followers = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Song(models.Model):
    spotify_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    title = models.CharField(max_length=240)
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True, related_name="songs")
    album = models.CharField(max_length=240, blank=True)
    genres = models.CharField(max_length=300, blank=True)
    mood = models.CharField(max_length=80, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    popularity = models.PositiveIntegerField(default=0)
    tempo = models.FloatField(default=0)
    energy = models.FloatField(default=0)
    danceability = models.FloatField(default=0)
    valence = models.FloatField(default=0)
    acousticness = models.FloatField(default=0)
    preview_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-popularity", "title"]

    def __str__(self):
        artist_name = self.artist.name if self.artist else "Unknown Artist"
        return f"{self.title} - {artist_name}"

    @property
    def recommendation_text(self):
        artist_name = self.artist.name if self.artist else ""
        return " ".join([self.title, artist_name, self.album, self.genres, self.mood])
