CURATED_POSTERS = {
    "3 idiots": "https://upload.wikimedia.org/wikipedia/en/d/df/3_idiots_poster.jpg",
    "dangal": "https://upload.wikimedia.org/wikipedia/en/9/99/Dangal_Poster.jpg",
    "gully boy": "https://upload.wikimedia.org/wikipedia/en/0/07/Gully_Boy_poster.jpg",
    "lagaan": "https://upload.wikimedia.org/wikipedia/en/b/b6/Lagaan.jpg",
    "zindagi na milegi dobara": "https://upload.wikimedia.org/wikipedia/en/3/3d/Zindaginamilegidobara.jpg",
    "inception": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg",
    "interstellar": "https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg",
    "the dark knight": "https://upload.wikimedia.org/wikipedia/en/8/8a/Dark_Knight.jpg",
    "arrival": "https://upload.wikimedia.org/wikipedia/en/d/df/Arrival%2C_Movie_Poster.jpg",
    "whiplash": "https://upload.wikimedia.org/wikipedia/en/0/01/Whiplash_poster.jpg",
    "the social network": "https://upload.wikimedia.org/wikipedia/en/8/8c/The_Social_Network_film_poster.png",
}


def curated_poster_for(title):
    return CURATED_POSTERS.get((title or "").strip().lower(), "")
