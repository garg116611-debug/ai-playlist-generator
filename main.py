import requests

TOKEN = input("Paste your Spotify Access Token: ")

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

params = {
    "q": "Punjabi workout",
    "type": "track",
    "limit": 5
}

url = "https://api.spotify.com/v1/search"

response = requests.get(url, headers=headers, params=params)

data = response.json()

print("\n🎶 Songs List:\n")

for i, item in enumerate(data["tracks"]["items"], start=1):
    song = item["name"]
    artist = item["artists"][0]["name"]
    print(f"{i}. {song} — {artist}")
