def discover_mood(mind_speed, lyrics, context):
    if mind_speed == "racing" and lyrics == "no" and context == "alone":
        return "focus"

    if mind_speed == "racing" and lyrics == "yes":
        return "energetic"

    if mind_speed == "normal" and lyrics == "yes" and context == "with people":
        return "chill"

    if mind_speed == "slow" and lyrics == "no" and context == "alone":
        return "calm"

    return "comfort"

if __name__ == "__main__":
    mood = discover_mood(
        mind_speed="racing",
        lyrics="no",
        context="alone"
    )
    print("Detected mood:", mood)
