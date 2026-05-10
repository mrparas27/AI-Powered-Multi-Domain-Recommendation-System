from django.urls import path

from apps.core import views

urlpatterns = [
    path("health/", views.health, name="api-health"),
    path("movies/", views.local_movies, name="api-movies"),
    path("movies/similar/<int:movie_id>/", views.api_similar_movies, name="api-similar-movies"),
    path("music/", views.local_music, name="api-music"),
    path("music/mood/", views.api_music_by_mood, name="api-music-mood"),
    path("jobs/", views.local_jobs, name="api-jobs"),
    path("jobs/resume-match/", views.api_resume_job_match, name="api-resume-job-match"),
    path("recommendations/", views.recommend, name="api-recommend"),
]
