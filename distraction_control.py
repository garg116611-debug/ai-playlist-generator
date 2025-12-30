def distraction_profile(level):
    if level == "low":
        return {
            "lyrics": "none",
            "popularity": "low",
            "energy": "soft"
        }

    if level == "medium":
        return {
            "lyrics": "some",
            "popularity": "medium",
            "energy": "medium"
        }

    return {
        "lyrics": "yes",
        "popularity": "high",
        "energy": "high"
    }

if __name__ == "__main__":
    profile = distraction_profile("low")
    print(profile)
