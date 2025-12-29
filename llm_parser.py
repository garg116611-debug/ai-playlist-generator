def parse_music_request(user_text):
    text = user_text.lower()
    keywords = []

    if "punjabi" in text:
        keywords.append("Punjabi")
    if "hindi" in text:
        keywords.append("Hindi")
    if "gym" in text:
        keywords.append("workout")
    if "low energy" in text:
        keywords.append("calm")
    if "high energy" in text:
        keywords.append("energetic")

    return " ".join(keywords)
