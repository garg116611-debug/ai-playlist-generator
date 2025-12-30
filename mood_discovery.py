def discover_mood(mind_speed, lyrics, context):
    if mind_speed == "racing":
        return "focus"
    if mind_speed == "slow":
        return "calm"
    return "balanced"
