import requests
import base64
import os
from dotenv import load_dotenv
from llm_parser import parse_music_request
from playlist_brain import build_search_query


load_dotenv()

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

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()   # important safety line
    return response.json()["access_token"]


def search_spotify(query):
    token = get_spotify_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": query,
        "type": "track",
        "limit": 5
    }

    url = "https://api.spotify.com/v1/search"
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()["tracks"]["items"]


# -------- PROGRAM START --------
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
search_query = parse_music_request(user_input)

print(f"\nSearching Spotify for: {search_query}\n")

songs = search_spotify(search_query)

print("🎶 Songs List:\n")
for i, song in enumerate(songs, start=1):
    print(f"{i}. {song['name']} — {song['artists'][0]['name']}")
