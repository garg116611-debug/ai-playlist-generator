"""
AI Playlist Generator - FastAPI Backend
Serves the web interface and handles playlist generation requests
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import requests
import base64
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from playlist_brain import build_search_query
from llm_parser import parse_natural_language, get_activity_suggestions, ACTIVITY_PRESETS

load_dotenv()

app = FastAPI(
    title="AI Playlist Generator",
    description="Generate Spotify playlists based on your mood",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- MODELS ----------
class MoodInput(BaseModel):
    mind_speed: str = "normal"
    lyrics: str = "sometimes"
    context: str = "alone"
    distraction: str = "medium"
    language: str = "any"      # NEW: Language filter
    genre: str = "any"         # NEW: Genre filter
    era: str = "any"           # NEW: Era/decade filter
    song_count: int = 5        # NEW: Number of songs

class NaturalLanguageInput(BaseModel):
    text: str
    language: str = "any"
    genre: str = "any"
    era: str = "any"
    song_count: int = 5

class PlaylistResponse(BaseModel):
    success: bool
    query: str
    songs: List[dict]
    generated_at: str

# ---------- CONFIGURATION ----------
# Language keywords - these are placed FIRST in search for better results
LANGUAGES = {
    "any": "",
    "english": "",  # Default, no keyword needed
    "hindi": "bollywood hindi",
    "punjabi": "punjabi bhangra",
    "tamil": "tamil kollywood",
    "telugu": "telugu tollywood",
    "korean": "kpop",
    "spanish": "reggaeton spanish",
    "japanese": "jpop japanese"
}

# Market codes for Spotify API - helps filter by region
MARKETS = {
    "any": None,
    "english": "US",
    "hindi": "IN",
    "punjabi": "IN",
    "tamil": "IN",
    "telugu": "IN",
    "korean": "KR",
    "spanish": "MX",
    "japanese": "JP"
}

GENRES = {
    "any": "",
    "pop": "pop",
    "rock": "rock",
    "hiphop": "hip hop rap",
    "electronic": "electronic edm",
    "classical": "classical",
    "jazz": "jazz",
    "rnb": "r&b soul",
    "bollywood": "bollywood filmi",
    "lofi": "lofi chill beats",
    "metal": "metal"
}

ERAS = {
    "any": "",
    "90s": "90s 1990s",
    "2000s": "2000s",
    "2010s": "2010s",
    "latest": "2023 2024 new"
}

# ---------- HISTORY STORAGE ----------
playlist_history = []

# ---------- SPOTIFY FUNCTIONS ----------
def get_spotify_token():
    """Get Spotify access token using client credentials"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Spotify credentials not configured")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    try:
        res = requests.post(url, headers=headers, data=data)
        res.raise_for_status()
        return res.json()["access_token"]
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Spotify auth failed: {str(e)}")


def search_spotify(query: str, token: str, limit: int = 5) -> List[dict]:
    """Search Spotify for tracks matching the query"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }

    url = "https://api.spotify.com/v1/search"
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        tracks = res.json()["tracks"]["items"]
        
        # Format response
        return [{
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "preview_url": track.get("preview_url"),
            "spotify_url": track["external_urls"]["spotify"],
            "duration_ms": track["duration_ms"]
        } for track in tracks]
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Spotify search failed: {str(e)}")


def get_audio_features(track_ids: List[str], token: str) -> List[dict]:
    """Get audio features for filtering"""
    if not track_ids:
        return []

    url = "https://api.spotify.com/v1/audio-features"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ids": ",".join(track_ids[:5])}

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()["audio_features"]
    except:
        return []


# ---------- API ROUTES ----------

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page"""
    return FileResponse("templates/index.html")


@app.post("/api/generate", response_model=PlaylistResponse)
async def generate_playlist(mood: MoodInput):
    """Generate playlist based on mood parameters"""
    
    # Build base search query
    search_query = build_search_query(
        mood.mind_speed,
        mood.lyrics,
        mood.context,
        mood.distraction
    )
    
    # Add language filter
    if mood.language in LANGUAGES and LANGUAGES[mood.language]:
        search_query = f"{search_query} {LANGUAGES[mood.language]}"
    
    # Add genre filter
    if mood.genre in GENRES and GENRES[mood.genre]:
        search_query = f"{search_query} {GENRES[mood.genre]}"
    
    # Add era filter
    if mood.era in ERAS and ERAS[mood.era]:
        search_query = f"{search_query} {ERAS[mood.era]}"
    
    # Get Spotify token and search (fetch more than needed for filtering)
    token = get_spotify_token()
    fetch_limit = min(mood.song_count * 2, 20)  # Fetch extra for filtering
    songs = search_spotify(search_query, token, limit=fetch_limit)
    
    # Filter for instrumental if requested
    if mood.lyrics == "no" and songs:
        track_ids = [s["id"] for s in songs]
        features = get_audio_features(track_ids, token)
        
        if features:
            filtered = []
            for song, feat in zip(songs, features):
                if feat and feat.get("instrumentalness", 0) > 0.5:
                    filtered.append(song)
            if filtered:
                songs = filtered
    
    # Take requested number of songs
    songs = songs[:mood.song_count]
    
    # Create response
    response = PlaylistResponse(
        success=True,
        query=search_query,
        songs=songs,
        generated_at=datetime.now().isoformat()
    )
    
    # Add to history
    playlist_history.append({
        "mood": mood.dict(),
        "query": search_query,
        "songs": [s["name"] for s in songs],
        "timestamp": response.generated_at
    })
    
    return response


@app.post("/api/generate-from-text")
async def generate_from_natural_language(input: NaturalLanguageInput):
    """Generate playlist from natural language description"""
    
    # Parse natural language
    result = parse_natural_language(input.text)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Could not understand input")
    
    # Generate playlist with parsed parameters + user overrides
    parsed = result["parsed"]
    parsed["language"] = input.language
    parsed["genre"] = input.genre
    parsed["era"] = input.era
    parsed["song_count"] = input.song_count
    
    mood = MoodInput(**parsed)
    playlist = await generate_playlist(mood)
    
    return {
        **playlist.dict(),
        "parsed_input": result
    }


@app.get("/api/config")
async def get_config():
    """Get available filter options"""
    return {
        "languages": list(LANGUAGES.keys()),
        "genres": list(GENRES.keys()),
        "eras": list(ERAS.keys()),
        "song_counts": [5, 10, 15]
    }


@app.get("/api/activities")
async def get_activities():
    """Get list of activity presets"""
    return {
        "activities": get_activity_suggestions(),
        "presets": ACTIVITY_PRESETS
    }


@app.get("/api/history")
async def get_history():
    """Get playlist generation history"""
    return {
        "history": playlist_history[-10:]  # Last 10
    }


@app.delete("/api/history")
async def clear_history():
    """Clear playlist history"""
    global playlist_history
    playlist_history = []
    return {"success": True, "message": "History cleared"}


# ---------- STARTUP ----------
if __name__ == "__main__":
    import uvicorn
    print(">> Starting AI Playlist Generator...")
    print(">> Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
