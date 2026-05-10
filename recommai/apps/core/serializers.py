def movie_dict(movie):
    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "overview": movie.overview,
        "genres": movie.genres,
        "cast": movie.cast,
        "director": movie.director,
        "release_year": movie.release_year,
        "runtime": movie.runtime,
        "rating": movie.rating,
        "popularity": movie.popularity,
        "poster_url": movie.poster_url,
    }


def song_dict(song):
    artist_name = song.artist.name if song.artist else ""
    return {
        "id": song.id,
        "spotify_id": song.spotify_id,
        "title": song.title,
        "artist": artist_name,
        "album": song.album,
        "genres": song.genres,
        "mood": song.mood,
        "duration_ms": song.duration_ms,
        "popularity": song.popularity,
        "tempo": song.tempo,
        "energy": song.energy,
        "danceability": song.danceability,
        "valence": song.valence,
        "preview_url": song.preview_url,
        "image_url": song.image_url,
    }


def job_dict(job):
    company_name = job.company.name if job.company else ""
    company_logo = job.company.logo_url if job.company else ""
    return {
        "id": job.id,
        "job_id": job.job_id,
        "title": job.title,
        "company": company_name,
        "company_logo": company_logo,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
        "skills": [skill.strip() for skill in job.skills.split(",") if skill.strip()],
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "job_type": job.job_type,
        "apply_url": job.apply_url,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
    }
