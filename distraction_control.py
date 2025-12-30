def distraction_profile(level):
    if level == "low":
        return {"energy": "soft", "lyrics": "none"}
    if level == "high":
        return {"energy": "high", "lyrics": "allowed"}
    return {"energy": "medium", "lyrics": "allowed"}
