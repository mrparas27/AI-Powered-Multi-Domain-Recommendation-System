import base64
import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

from apps.external_apis.models import APICache, APIRequestLog


class ExternalAPIError(RuntimeError):
    pass


class BaseClient:
    provider = "base"
    timeout = 20

    def _cache_key(self, endpoint, params):
        query = urlencode(sorted((params or {}).items()), doseq=True)
        return f"{self.provider}:{endpoint}:{query}"

    def get_cached(self, endpoint, params, fetcher):
        key = self._cache_key(endpoint, params)
        cached = APICache.objects.filter(key=key, expires_at__gt=timezone.now()).first()
        if cached:
            return cached.payload
        payload = fetcher()
        APICache.objects.update_or_create(
            key=key,
            defaults={
                "provider": self.provider,
                "payload": payload,
                "expires_at": timezone.now() + timezone.timedelta(seconds=settings.EXTERNAL_APIS["CACHE_TTL_SECONDS"]),
            },
        )
        return payload

    def request(self, method, url, **kwargs):
        start = time.perf_counter()
        status_code = None
        try:
            headers = kwargs.pop("headers", {}) or {}
            headers.setdefault("User-Agent", "RecommAI/2.0")
            kwargs["headers"] = headers
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            status_code = response.status_code
            response.raise_for_status()
            success = True
            error = ""
            return response.json()
        except requests.RequestException as exc:
            success = False
            error = str(exc)
            if status_code in {401, 403}:
                message = f"{self.provider} rejected the configured credentials or access scope."
            elif isinstance(exc, requests.Timeout):
                message = f"{self.provider} timed out. Showing fallback data when available."
            else:
                message = f"{self.provider} is unavailable right now. Showing fallback data when available."
            raise ExternalAPIError(message) from exc
        finally:
            APIRequestLog.objects.create(
                provider=self.provider,
                endpoint=url[:260],
                status_code=status_code,
                success=success if "success" in locals() else False,
                error=error if "error" in locals() else "Unexpected error",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )


class TMDBClient(BaseClient):
    provider = "TMDB"
    base_url = "https://api.themoviedb.org/3"
    image_base = "https://image.tmdb.org/t/p/w500"
    timeout = 6

    def _params(self, params=None):
        api_key = settings.EXTERNAL_APIS["TMDB_API_KEY"]
        if not api_key:
            raise ExternalAPIError("TMDB_API_KEY is not configured.")
        return {"api_key": api_key, **(params or {})}

    def search_movies(self, query, year=None):
        params = self._params({"query": query})
        if year:
            params["year"] = year
        payload = self.get_cached("search/movie", params, lambda: self.request("GET", f"{self.base_url}/search/movie", params=params))
        return [self.normalize_movie(item) for item in payload.get("results", [])]

    def enrich_search_result(self, movie):
        tmdb_id = movie.get("tmdb_id")
        if not tmdb_id:
            return movie
        try:
            detailed = self.details(tmdb_id)
        except ExternalAPIError:
            return movie
        return {**movie, **{key: value for key, value in detailed.items() if value not in ("", None, [])}}

    def trending(self, window="week"):
        window = "day" if window == "day" else "week"
        params = self._params()
        payload = self.get_cached(f"trending/movie/{window}", params, lambda: self.request("GET", f"{self.base_url}/trending/movie/{window}", params=params))
        return [self.normalize_movie(item) for item in payload.get("results", [])]

    def details(self, tmdb_id):
        params = self._params({"append_to_response": "credits"})
        payload = self.get_cached(f"movie/{tmdb_id}", params, lambda: self.request("GET", f"{self.base_url}/movie/{tmdb_id}", params=params))
        return self.normalize_movie(payload, detailed=True)

    def similar(self, tmdb_id):
        params = self._params()
        payload = self.get_cached(f"movie/{tmdb_id}/similar", params, lambda: self.request("GET", f"{self.base_url}/movie/{tmdb_id}/similar", params=params))
        return [self.normalize_movie(item) for item in payload.get("results", [])]

    def normalize_movie(self, item, detailed=False):
        release_date = item.get("release_date") or ""
        genres = item.get("genres") or []
        crew = (item.get("credits") or {}).get("crew", [])
        cast = (item.get("credits") or {}).get("cast", [])
        director = next((person.get("name") for person in crew if person.get("job") == "Director"), "")
        return {
            "tmdb_id": item.get("id"),
            "title": item.get("title") or item.get("name", ""),
            "overview": item.get("overview", ""),
            "release_year": int(release_date[:4]) if release_date[:4].isdigit() else None,
            "rating": item.get("vote_average") or 0,
            "popularity": item.get("popularity") or 0,
            "poster_url": f"{self.image_base}{item.get('poster_path')}" if item.get("poster_path") else "",
            "vote_count": item.get("vote_count") or 0,
            "genres": ", ".join(g["name"] for g in genres) if detailed else "",
            "director": director,
            "cast": ", ".join(person.get("name", "") for person in cast[:8]),
            "runtime": item.get("runtime"),
        }


class SpotifyClient(BaseClient):
    provider = "Spotify"
    base_url = "https://api.spotify.com/v1"
    token_url = "https://accounts.spotify.com/api/token"

    def token(self):
        client_id = settings.EXTERNAL_APIS["SPOTIFY_CLIENT_ID"]
        client_secret = settings.EXTERNAL_APIS["SPOTIFY_CLIENT_SECRET"]
        if not client_id or not client_secret:
            raise ExternalAPIError("Spotify credentials are not configured.")
        raw = f"{client_id}:{client_secret}".encode()
        headers = {"Authorization": "Basic " + base64.b64encode(raw).decode()}
        payload = self.request("POST", self.token_url, headers=headers, data={"grant_type": "client_credentials"})
        return payload["access_token"]

    def _headers(self):
        return {"Authorization": f"Bearer {self.token()}"}

    def search_tracks(self, query, limit=10, market="IN"):
        params = {"q": query, "type": "track", "limit": limit, "market": market or "IN"}
        payload = self.get_cached("search/tracks", params, lambda: self.request("GET", f"{self.base_url}/search", headers=self._headers(), params=params))
        return [self.normalize_track(track) for track in payload.get("tracks", {}).get("items", [])]

    def trending_tracks(self, country="US", limit=10):
        params = {"q": "tag:new", "type": "track", "market": country, "limit": limit}
        payload = self.get_cached("music/trending", params, lambda: self.request("GET", f"{self.base_url}/search", headers=self._headers(), params=params))
        return [self.normalize_track(track) for track in payload.get("tracks", {}).get("items", [])]

    def track_details(self, spotify_id):
        payload = self.get_cached(f"tracks/{spotify_id}", {}, lambda: self.request("GET", f"{self.base_url}/tracks/{spotify_id}", headers=self._headers()))
        return self.normalize_track(payload)

    def search_artists(self, query, limit=10):
        params = {"q": query, "type": "artist", "limit": limit, "market": "US"}
        payload = self.get_cached("search/artists", params, lambda: self.request("GET", f"{self.base_url}/search", headers=self._headers(), params=params))
        return [self.normalize_artist(artist) for artist in payload.get("artists", {}).get("items", [])]

    def normalize_track(self, track):
        images = track.get("album", {}).get("images", [])
        artists = track.get("artists") or []
        return {
            "spotify_id": track.get("id"),
            "title": track.get("name", ""),
            "artist": artists[0].get("name", "") if artists else "",
            "album": track.get("album", {}).get("name", ""),
            "duration_ms": track.get("duration_ms") or 0,
            "popularity": track.get("popularity") or 0,
            "preview_url": track.get("preview_url") or "",
            "image_url": images[0]["url"] if images else "",
        }

    def normalize_artist(self, artist):
        images = artist.get("images") or []
        return {
            "spotify_id": artist.get("id"),
            "name": artist.get("name", ""),
            "genres": ", ".join(artist.get("genres") or []),
            "popularity": artist.get("popularity") or 0,
            "image_url": images[0]["url"] if images else "",
            "followers": artist.get("followers", {}).get("total") or 0,
        }


class ITunesClient(BaseClient):
    provider = "iTunes"
    base_url = "https://itunes.apple.com/search"
    timeout = 5

    def search_tracks(self, query, limit=10, country="IN"):
        params = {"term": query, "media": "music", "entity": "song", "limit": limit, "country": country or "IN"}
        payload = self.get_cached("search", params, lambda: self.request("GET", self.base_url, params=params))
        return [self.normalize_track(track) for track in payload.get("results", [])]

    def search_movies(self, query, limit=10, country="IN"):
        params = {"term": query, "media": "movie", "entity": "movie", "limit": limit, "country": country or "IN"}
        payload = self.get_cached("movie/search", params, lambda: self.request("GET", self.base_url, params=params))
        return [self.normalize_movie(movie) for movie in payload.get("results", [])]

    def normalize_track(self, track):
        image_url = (track.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
        return {
            "spotify_id": f"itunes_{track.get('trackId')}" if track.get("trackId") else "",
            "title": track.get("trackName", ""),
            "artist": track.get("artistName", ""),
            "album": track.get("collectionName", ""),
            "duration_ms": track.get("trackTimeMillis") or 0,
            "popularity": 75,
            "preview_url": track.get("previewUrl", ""),
            "image_url": image_url,
            "genres": track.get("primaryGenreName", ""),
            "mood": "",
        }

    def normalize_movie(self, movie):
        image_url = (movie.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
        release_date = movie.get("releaseDate") or ""
        return {
            "tmdb_id": movie.get("trackId"),
            "title": movie.get("trackName", ""),
            "overview": movie.get("longDescription") or movie.get("shortDescription") or "",
            "release_year": int(release_date[:4]) if release_date[:4].isdigit() else None,
            "rating": 0,
            "popularity": 70,
            "poster_url": image_url,
            "genres": movie.get("primaryGenreName", ""),
            "director": movie.get("artistName", ""),
            "cast": "",
            "runtime": int((movie.get("trackTimeMillis") or 0) / 60000) if movie.get("trackTimeMillis") else None,
        }


class WikipediaMovieClient(BaseClient):
    provider = "Wikipedia"
    base_url = "https://en.wikipedia.org/w/api.php"
    timeout = 8

    def search_movies(self, query, limit=10):
        exact = self.movie_details_by_title(query)
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{query} film",
            "srlimit": limit,
        }
        search_payload = self.get_cached(
            "search/movie",
            search_params,
            lambda: self.request("GET", self.base_url, params=search_params),
        )
        page_ids = [str(row.get("pageid")) for row in search_payload.get("query", {}).get("search", []) if row.get("pageid")]
        if not page_ids:
            return []
        detail_params = {
            "action": "query",
            "format": "json",
            "pageids": "|".join(page_ids),
            "prop": "extracts|pageimages",
            "exintro": "1",
            "explaintext": "1",
            "piprop": "thumbnail",
            "pithumbsize": "500",
        }
        detail_payload = self.get_cached(
            "movie/details",
            detail_params,
            lambda: self.request("GET", self.base_url, params=detail_params),
        )
        pages = detail_payload.get("query", {}).get("pages", {})
        movies = [self.normalize_movie(page) for page in pages.values() if page.get("title")]
        if exact:
            movies = [exact] + [movie for movie in movies if movie["title"].lower() != exact["title"].lower()]
        query_norm = query.strip().lower()
        movies.sort(key=lambda movie: (
            0 if movie["title"].lower() == query_norm else 1 if query_norm in movie["title"].lower() else 2,
            -movie.get("popularity", 0),
        ))
        return movies

    def movie_details_by_title(self, title):
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts|pageimages",
            "exintro": "1",
            "explaintext": "1",
            "piprop": "thumbnail",
            "pithumbsize": "500",
        }
        payload = self.get_cached("movie/title", params, lambda: self.request("GET", self.base_url, params=params))
        pages = payload.get("query", {}).get("pages", {})
        page = next((value for value in pages.values() if not value.get("missing")), None)
        return self.normalize_movie(page) if page else None

    def normalize_movie(self, page):
        page_id = int(page.get("pageid") or 0)
        return {
            "tmdb_id": 800000000 + page_id if page_id else None,
            "title": page.get("title", ""),
            "overview": page.get("extract", ""),
            "release_year": None,
            "rating": 0,
            "popularity": 65,
            "poster_url": (page.get("thumbnail") or {}).get("source", ""),
            "genres": "Film",
            "director": "",
            "cast": "",
            "runtime": None,
        }


class JobHunterClient(BaseClient):
    provider = "JSearch"
    base_url = "https://jsearch.p.rapidapi.com"

    def _headers(self):
        api_key = settings.EXTERNAL_APIS["JOBHUNTER_API_KEY"]
        if not api_key:
            raise ExternalAPIError("JOBHUNTER_API_KEY is not configured.")
        return {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

    def search_jobs(self, query, location="", job_type=""):
        search = " ".join(part for part in [query, location or "India", job_type] if part).strip()
        params = {"query": search, "page": "1", "num_pages": "1", "country": "IN"}
        payload = self.get_cached("search", params, lambda: self.request("GET", f"{self.base_url}/search", headers=self._headers(), params=params))
        return [self.normalize_job(item) for item in payload.get("data", payload.get("results", payload.get("jobs", [])))]

    def job_details(self, job_id):
        params = {"job_id": job_id}
        payload = self.get_cached("job-details", params, lambda: self.request("GET", f"{self.base_url}/job-details", headers=self._headers(), params=params))
        data = payload.get("data") or []
        return self.normalize_job(data[0] if data else payload)

    def search_companies(self, query):
        params = {"q": query}
        payload = self.get_cached("companies/search", params, lambda: self.request("GET", f"{self.base_url}/companies/search", headers=self._headers(), params=params))
        return payload.get("results", payload.get("companies", []))

    def normalize_job(self, item):
        skills = item.get("skills") or item.get("job_required_skills") or []
        if isinstance(skills, str):
            skills = [skill.strip() for skill in skills.split(",") if skill.strip()]
        apply_options = item.get("apply_options") or []
        apply_url = item.get("job_apply_link") or item.get("apply_url") or ""
        if not apply_url and apply_options:
            apply_url = apply_options[0].get("apply_link", "")
        min_salary = item.get("job_min_salary") or item.get("salary_min")
        max_salary = item.get("job_max_salary") or item.get("salary_max")
        return {
            "job_id": str(item.get("job_id") or item.get("id") or ""),
            "title": item.get("job_title") or item.get("title", ""),
            "company": item.get("employer_name") or (item.get("company", {}).get("name") if isinstance(item.get("company"), dict) else item.get("company", "")),
            "company_logo": item.get("employer_logo") or "",
            "location": item.get("job_city") or item.get("job_location") or item.get("location", ""),
            "description": item.get("job_description") or item.get("description", ""),
            "requirements": item.get("job_required_experience", {}).get("required_experience_in_months") if isinstance(item.get("job_required_experience"), dict) else item.get("requirements", ""),
            "salary_min": int(min_salary) if isinstance(min_salary, (int, float)) else None,
            "salary_max": int(max_salary) if isinstance(max_salary, (int, float)) else None,
            "job_type": item.get("job_employment_type") or item.get("job_type") or item.get("type", ""),
            "posted_at": item.get("posted_at"),
            "skills": skills,
            "apply_url": apply_url,
        }


class GitHubClient(BaseClient):
    provider = "GitHub"
    base_url = "https://api.github.com"

    def search_repositories(self, query, limit=10):
        headers = {}
        if settings.EXTERNAL_APIS["GITHUB_TOKEN"]:
            headers["Authorization"] = f"Bearer {settings.EXTERNAL_APIS['GITHUB_TOKEN']}"
        params = {"q": query, "per_page": limit, "sort": "stars"}
        payload = self.get_cached("search/repositories", params, lambda: self.request("GET", f"{self.base_url}/search/repositories", headers=headers, params=params))
        return [{
            "name": repo.get("full_name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "url": repo.get("html_url"),
        } for repo in payload.get("items", [])]


class SerpAPIClient(BaseClient):
    provider = "SerpAPI"
    base_url = "https://serpapi.com/search.json"

    def search(self, query, limit=10):
        api_key = settings.EXTERNAL_APIS["SERPAPI_API_KEY"]
        if not api_key:
            raise ExternalAPIError("SERPAPI_API_KEY is not configured.")
        params = {"q": query, "api_key": api_key, "num": limit}
        payload = self.get_cached("search", params, lambda: self.request("GET", self.base_url, params=params))
        return [{
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
        } for item in payload.get("organic_results", [])[:limit]]

    def search_jobs(self, query, location="", limit=10):
        api_key = settings.EXTERNAL_APIS["SERPAPI_API_KEY"]
        if not api_key:
            raise ExternalAPIError("SERPAPI_API_KEY is not configured.")
        params = {"engine": "google_jobs", "q": query, "location": location or "India", "api_key": api_key}
        payload = self.get_cached("google_jobs", params, lambda: self.request("GET", self.base_url, params=params))
        return [self.normalize_job(item) for item in payload.get("jobs_results", [])[:limit]]

    def normalize_job(self, item):
        apply_options = item.get("apply_options") or []
        detected = item.get("detected_extensions") or {}
        return {
            "job_id": item.get("job_id") or item.get("job_id_token") or item.get("title", ""),
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "company_logo": item.get("thumbnail", ""),
            "location": item.get("location", ""),
            "description": item.get("description", ""),
            "requirements": "",
            "salary_min": None,
            "salary_max": None,
            "job_type": detected.get("schedule_type", ""),
            "posted_at": None,
            "skills": [],
            "apply_url": apply_options[0].get("link", "") if apply_options else item.get("share_link", ""),
        }


class WeatherAPIClient(BaseClient):
    provider = "WeatherAPI"
    base_url = "https://api.weatherapi.com/v1/current.json"

    def current(self, location):
        api_key = settings.EXTERNAL_APIS["WEATHER_API_KEY"]
        if not api_key:
            raise ExternalAPIError("WEATHER_API_KEY is not configured.")
        params = {"key": api_key, "q": location, "aqi": "no"}
        payload = self.get_cached("current", params, lambda: self.request("GET", self.base_url, params=params))
        current = payload.get("current", {})
        place = payload.get("location", {})
        return {
            "location": place.get("name"),
            "region": place.get("region"),
            "country": place.get("country"),
            "temperature_c": current.get("temp_c"),
            "condition": (current.get("condition") or {}).get("text"),
            "humidity": current.get("humidity"),
            "wind_kph": current.get("wind_kph"),
        }
