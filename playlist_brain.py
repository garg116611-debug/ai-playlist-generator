from mood_discovery import discover_mood
from distraction_control import distraction_profile


def build_search_query(mind_speed, lyrics, context, distraction):
    mood = discover_mood(mind_speed, lyrics, context)
    profile = distraction_profile(distraction)

    keywords = []

    # Energy / mood control
    if profile["energy"] == "high":
        keywords.append("energetic")
    elif profile["energy"] == "soft":
        keywords.append("calm")

    # Core mood
    keywords.append(mood)

    # Lyrics strictly user-controlled
    if lyrics == "no":
        keywords.append("instrumental")

    return " ".join(keywords)
