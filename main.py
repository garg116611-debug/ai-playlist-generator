
from llm_parser import parse_music_request

import requests

TOKEN = input("Paste your Spotify Access Token:")

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

user_input = input("Enter your playlist request: ")

search_query = parse_music_request(user_input)
print(f"Searching Spotify for: {search_query}")

params = {
    "q": search_query,
    "type": "track",
    "limit": 5
}



url = "https://api.spotify.com/v1/search"

response = requests.get(url, headers=headers, params=params)

data = response.json()

if "tracks" not in data:
    print("❌ Error from Spotify API:")
    print(data)
else:
    print("\n🎶 Songs List:\n")
    for i, item in enumerate(data["tracks"]["items"], start=1):
        song = item["name"]
        artist = item["artists"][0]["name"]
        print(f"{i}. {song} — {artist}")

