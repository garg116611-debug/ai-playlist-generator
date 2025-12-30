import requests
import base64
import os
from dotenv import load_dotenv
from playlist_brain import build_search_query

load_dotenv()

# ---------- SPOTIFY AUTH ----------
def get_spotify_token():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    res = requests.post(url, headers=headers, data=data)
    res.raise_for_status()
    return res.json()["access_token"]


# ---------- SPOTIFY SEARCH ----------
def search_spotify(query, token, limit=5):
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }

    url = "https://api.spotify.com/v1/search"
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()["tracks"]["items"]


# ---------- AUDIO FEATURES (SAFE) ----------
def get_audio_features(track_ids, token):
    if not track_ids:
        return []

    url = "https://api.spotify.com/v1/audio-features"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"ids": ",".join(track_ids[:3])}  # safety limit

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()["audio_features"]
    except:
        return []


# ---------- PROGRAM START ----------
print("Answer the following questions:\n")

mind_speed = input("How is your mind? (racing / normal / slow): ").lower()
lyrics = input("Do you want lyrics? (yes / sometimes / no): ").lower()
context = input("Are you alone or with people? (alone / with people): ").lower()
distraction = input("Distraction level? (low / medium / high): ").lower()

search_query = build_search_query(
    mind_speed,
    lyrics,
    context,
    distraction
)

print(f"\nSearching Spotify for: {search_query}\n")

token = get_spotify_token()
songs = search_spotify(search_query, token)

track_ids = [s["id"] for s in songs if s.get("id")]
features = get_audio_features(track_ids, token)

# ---------- FILTER ----------
final_songs = []

if lyrics == "no" and features:
    for song, feat in zip(songs, features):
        if feat and feat["instrumentalness"] > 0.7 and feat["speechiness"] < 0.3:
            final_songs.append(song)
else:
    final_songs = songs

# ---------- OUTPUT ----------
print("🎶 Songs List:\n")
for i, song in enumerate(final_songs[:5], start=1):
    print(f"{i}. {song['name']} — {song['artists'][0]['name']}")
