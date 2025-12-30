from mood_discovery import discover_mood
from distraction_control import distraction_profile

def build_search_query(mind_speed, lyrics, context, distraction):
    # Step 1: discover mood
    mood = discover_mood(mind_speed, lyrics, context)

    # Step 2: get distraction profile
    profile = distraction_profile(distraction)

    # Step 3: build Spotify-friendly keywords
    keywords = []

    keywords.append(mood)

    if profile["energy"] == "high":
        keywords.append("energetic")
    if profile["energy"] == "soft":
        keywords.append("calm")

    if profile["lyrics"] == "none":
        keywords.append("instrumental")

    return " ".join(keywords)

if __name__ == "__main__":
    query = build_search_query(
        mind_speed="racing",
        lyrics="no",
        context="alone",
        distraction="low"
    )

    print("Spotify search query:", query)
