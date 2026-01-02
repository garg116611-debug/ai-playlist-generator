"""
AI Playlist Generator - Vercel Serverless Entry Point
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

# ---------- MODELS ----------
class MoodInput(BaseModel):
    mind_speed: str = "normal"
    lyrics: str = "sometimes"
    context: str = "alone"
    distraction: str = "medium"
    language: str = "any"
    genre: str = "any"
    era: str = "any"
    song_count: int = 5

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
LANGUAGES = {
    "any": "",
    "english": "",
    "hindi": "bollywood hindi",
    "punjabi": "punjabi bhangra",
    "tamil": "tamil kollywood",
    "telugu": "telugu tollywood",
    "korean": "kpop",
    "spanish": "reggaeton spanish",
    "japanese": "jpop japanese"
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

# Activity presets
ACTIVITY_PRESETS = {
    "studying": {"mind_speed": "racing", "lyrics": "no", "context": "alone", "distraction": "low"},
    "coding": {"mind_speed": "racing", "lyrics": "no", "context": "alone", "distraction": "low"},
    "workout": {"mind_speed": "racing", "lyrics": "yes", "context": "alone", "distraction": "high"},
    "sleeping": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "meditation": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "party": {"mind_speed": "racing", "lyrics": "yes", "context": "with people", "distraction": "high"},
    "driving": {"mind_speed": "normal", "lyrics": "yes", "context": "alone", "distraction": "medium"},
    "sad": {"mind_speed": "slow", "lyrics": "yes", "context": "alone", "distraction": "low"},
    "happy": {"mind_speed": "racing", "lyrics": "yes", "context": "with people", "distraction": "high"},
    "cooking": {"mind_speed": "normal", "lyrics": "yes", "context": "alone", "distraction": "medium"},
    "romantic": {"mind_speed": "slow", "lyrics": "yes", "context": "with people", "distraction": "low"},
    "chill": {"mind_speed": "slow", "lyrics": "sometimes", "context": "alone", "distraction": "low"}
}

# ---------- HISTORY STORAGE ----------
playlist_history = []

# ---------- SPOTIFY FUNCTIONS ----------
def get_spotify_token():
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


def build_search_query(mind_speed, lyrics, context, distraction):
    keywords = []
    
    if mind_speed == "racing":
        keywords.extend(["energetic", "upbeat", "fast"])
    elif mind_speed == "slow":
        keywords.extend(["calm", "relaxing", "slow"])
    else:
        keywords.extend(["moderate", "balanced"])
    
    if lyrics == "no":
        keywords.append("instrumental")
    elif lyrics == "yes":
        keywords.append("vocal")
    
    if context == "with people":
        keywords.append("party")
    
    if distraction == "low":
        keywords.extend(["ambient", "focus"])
    elif distraction == "high":
        keywords.extend(["dance", "exciting"])
    
    return " ".join(keywords)


def parse_natural_language(text):
    text_lower = text.lower()
    
    # Check for activity presets
    for activity, params in ACTIVITY_PRESETS.items():
        if activity in text_lower:
            return {
                "success": True,
                "parsed": params.copy(),
                "detected_activity": activity
            }
    
    # Default parsing
    params = {
        "mind_speed": "normal",
        "lyrics": "sometimes",
        "context": "alone",
        "distraction": "medium"
    }
    
    if any(w in text_lower for w in ["fast", "energy", "pump", "workout", "party"]):
        params["mind_speed"] = "racing"
        params["distraction"] = "high"
    elif any(w in text_lower for w in ["calm", "relax", "sleep", "slow", "chill"]):
        params["mind_speed"] = "slow"
        params["distraction"] = "low"
    
    if any(w in text_lower for w in ["focus", "study", "work", "concentrate"]):
        params["lyrics"] = "no"
        params["distraction"] = "low"
    
    if any(w in text_lower for w in ["friends", "people", "party", "social"]):
        params["context"] = "with people"
    
    return {
        "success": True,
        "parsed": params,
        "detected_activity": None
    }


# ---------- API ROUTES ----------

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")


@app.post("/api/generate", response_model=PlaylistResponse)
async def generate_playlist(mood: MoodInput):
    search_query = build_search_query(
        mood.mind_speed,
        mood.lyrics,
        mood.context,
        mood.distraction
    )
    
    if mood.language in LANGUAGES and LANGUAGES[mood.language]:
        search_query = f"{search_query} {LANGUAGES[mood.language]}"
    
    if mood.genre in GENRES and GENRES[mood.genre]:
        search_query = f"{search_query} {GENRES[mood.genre]}"
    
    if mood.era in ERAS and ERAS[mood.era]:
        search_query = f"{search_query} {ERAS[mood.era]}"
    
    token = get_spotify_token()
    fetch_limit = min(mood.song_count * 2, 20)
    songs = search_spotify(search_query, token, limit=fetch_limit)
    
    songs = songs[:mood.song_count]
    
    response = PlaylistResponse(
        success=True,
        query=search_query,
        songs=songs,
        generated_at=datetime.now().isoformat()
    )
    
    playlist_history.append({
        "mood": mood.dict(),
        "query": search_query,
        "songs": [s["name"] for s in songs],
        "timestamp": response.generated_at
    })
    
    return response


@app.post("/api/generate-from-text")
async def generate_from_natural_language(input: NaturalLanguageInput):
    result = parse_natural_language(input.text)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Could not understand input")
    
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
    return {
        "languages": list(LANGUAGES.keys()),
        "genres": list(GENRES.keys()),
        "eras": list(ERAS.keys()),
        "song_counts": [5, 10, 15]
    }


@app.get("/api/activities")
async def get_activities():
    return {
        "activities": list(ACTIVITY_PRESETS.keys()),
        "presets": ACTIVITY_PRESETS
    }


@app.get("/api/history")
async def get_history():
    return {"history": playlist_history[-10:]}


@app.delete("/api/history")
async def clear_history():
    global playlist_history
    playlist_history = []
    return {"success": True, "message": "History cleared"}


# ---------- SPOTIFY OAUTH (Cookie-based for Vercel) ----------
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
import urllib.parse

REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "https://moodtunes-sigma.vercel.app/callback")
SCOPES = "playlist-modify-public playlist-modify-private user-read-private"


@app.get("/login")
async def spotify_login():
    """Redirect to Spotify authorization"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={urllib.parse.quote(SCOPES)}"
    )
    
    return RedirectResponse(url=auth_url)


@app.get("/callback")
async def spotify_callback(code: str = None, error: str = None):
    """Handle Spotify OAuth callback - store token in cookie"""
    
    if error:
        return RedirectResponse(url="/?error=auth_failed")
    
    if not code:
        return RedirectResponse(url="/?error=no_code")
    
    # Exchange code for tokens
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        res = requests.post(token_url, headers=headers, data=data)
        res.raise_for_status()
        tokens = res.json()
        
        # Get user profile
        user_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_res = requests.get("https://api.spotify.com/v1/me", headers=user_headers)
        user_data = user_res.json()
        
        user_id = user_data.get("id", "default")
        display_name = user_data.get("display_name", "User")
        access_token = tokens["access_token"]
        
        # Create response with cookies
        response = RedirectResponse(url=f"/?logged_in={user_id}&name={urllib.parse.quote(display_name)}")
        
        # Set HTTP-only cookies (secure in production)
        response.set_cookie(
            key="spotify_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600  # 1 hour
        )
        response.set_cookie(
            key="spotify_user",
            value=user_id,
            httponly=False,  # JS can read this
            secure=True,
            samesite="lax",
            max_age=3600
        )
        response.set_cookie(
            key="spotify_name",
            value=display_name,
            httponly=False,
            secure=True,
            samesite="lax",
            max_age=3600
        )
        
        return response
        
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}")


@app.get("/api/me")
async def get_current_user(request: Request):
    """Get logged in user info from cookie"""
    user_id = request.cookies.get("spotify_user")
    display_name = request.cookies.get("spotify_name")
    token = request.cookies.get("spotify_token")
    
    if user_id and token:
        return {
            "logged_in": True,
            "user_id": user_id,
            "display_name": display_name or "User"
        }
    return {"logged_in": False}


class SavePlaylistRequest(BaseModel):
    playlist_name: str
    track_ids: List[str]


@app.post("/api/save-playlist")
async def save_playlist(req: SavePlaylistRequest, request: Request):
    """Save playlist to user's Spotify account using cookie token"""
    
    access_token = request.cookies.get("spotify_token")
    spotify_user_id = request.cookies.get("spotify_user")
    
    if not access_token or not spotify_user_id:
        raise HTTPException(status_code=401, detail="Not logged in. Please login with Spotify first.")
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    try:
        # Create playlist
        create_url = f"https://api.spotify.com/v1/users/{spotify_user_id}/playlists"
        create_data = {
            "name": req.playlist_name,
            "description": "Created by MoodTunes AI 🎵",
            "public": True
        }
        
        create_res = requests.post(create_url, headers=headers, json=create_data)
        
        if create_res.status_code == 401:
            raise HTTPException(status_code=401, detail="Session expired. Please login again.")
        
        create_res.raise_for_status()
        playlist = create_res.json()
        
        # Add tracks
        add_url = f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks"
        track_uris = [f"spotify:track:{tid}" for tid in req.track_ids]
        
        add_res = requests.post(add_url, headers=headers, json={"uris": track_uris})
        add_res.raise_for_status()
        
        return {
            "success": True,
            "playlist_id": playlist["id"],
            "playlist_url": playlist["external_urls"]["spotify"],
            "message": f"Playlist '{req.playlist_name}' saved to Spotify!"
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to save playlist: {str(e)}")


@app.get("/logout")
async def logout():
    """Logout user by clearing cookies"""
    response = RedirectResponse(url="/")
    response.delete_cookie("spotify_token")
    response.delete_cookie("spotify_user")
    response.delete_cookie("spotify_name")
    return response

