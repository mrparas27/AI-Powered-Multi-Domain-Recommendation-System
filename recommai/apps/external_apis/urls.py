from django.urls import path

from apps.external_apis import views

urlpatterns = [
    path("status/", views.provider_status, name="external-provider-status"),
    path("movies/search/", views.movie_search, name="external-movie-search"),
    path("movies/trending/", views.movie_trending, name="external-movie-trending"),
    path("movies/<int:tmdb_id>/", views.movie_details, name="external-movie-details"),
    path("movies/<int:tmdb_id>/similar/", views.movie_similar, name="external-movie-similar"),
    path("music/search/", views.music_search, name="external-music-search"),
    path("music/trending/", views.music_trending, name="external-music-trending"),
    path("tracks/<str:spotify_id>/", views.track_details, name="external-track-details"),
    path("artists/search/", views.artist_search, name="external-artist-search"),
    path("jobs/search/", views.job_search, name="external-job-search"),
    path("jobs/<str:job_id>/", views.job_details, name="external-job-details"),
    path("companies/search/", views.company_search, name="external-company-search"),
    path("github/repositories/", views.github_repositories, name="external-github-repositories"),
    path("web/search/", views.web_search, name="external-web-search"),
    path("weather/current/", views.weather_current, name="external-weather-current"),
    path("import/movies/", views.import_movies, name="external-import-movies"),
    path("import/songs/", views.import_songs, name="external-import-songs"),
    path("import/jobs/", views.import_jobs, name="external-import-jobs"),
]
