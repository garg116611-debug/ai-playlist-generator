"""
Enhanced LLM Parser for Natural Language Mood Detection
Uses keyword matching and sentiment analysis to interpret user's natural language input
"""

# Mood keywords mapping
MOOD_KEYWORDS = {
    "racing": ["stressed", "anxious", "overwhelmed", "busy", "chaotic", "racing", "fast", "hyper", "energetic", "wired", "restless"],
    "slow": ["tired", "exhausted", "sleepy", "lazy", "drained", "slow", "lethargic", "calm", "peaceful", "relaxed", "chill"],
    "normal": ["fine", "okay", "normal", "balanced", "neutral", "average", "moderate", "stable"]
}

LYRICS_KEYWORDS = {
    "yes": ["lyrics", "sing", "vocal", "words", "singing", "voice", "melody"],
    "no": ["instrumental", "no lyrics", "no words", "beats", "classical", "ambient", "piano", "guitar only"],
    "sometimes": ["maybe", "sometimes", "either", "both", "don't mind", "doesn't matter"]
}

CONTEXT_KEYWORDS = {
    "alone": ["alone", "solo", "myself", "private", "personal", "solitude", "by myself"],
    "with people": ["friends", "party", "group", "people", "social", "hangout", "together", "gathering", "crowd"]
}

DISTRACTION_KEYWORDS = {
    "low": ["focus", "concentrate", "study", "work", "productive", "deep work", "coding", "reading", "writing"],
    "medium": ["background", "casual", "light work", "browsing", "relaxing"],
    "high": ["dance", "workout", "exercise", "party", "driving", "gym", "running", "cardio", "energy"]
}

# Activity to mood mapping for quick suggestions
ACTIVITY_PRESETS = {
    "studying": {"mind_speed": "racing", "lyrics": "no", "context": "alone", "distraction": "low"},
    "working": {"mind_speed": "racing", "lyrics": "no", "context": "alone", "distraction": "low"},
    "coding": {"mind_speed": "racing", "lyrics": "no", "context": "alone", "distraction": "low"},
    "relaxing": {"mind_speed": "slow", "lyrics": "yes", "context": "alone", "distraction": "medium"},
    "sleeping": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "party": {"mind_speed": "racing", "lyrics": "yes", "context": "with people", "distraction": "high"},
    "workout": {"mind_speed": "racing", "lyrics": "yes", "context": "alone", "distraction": "high"},
    "gym": {"mind_speed": "racing", "lyrics": "yes", "context": "alone", "distraction": "high"},
    "driving": {"mind_speed": "normal", "lyrics": "yes", "context": "alone", "distraction": "high"},
    "meditation": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "yoga": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "cooking": {"mind_speed": "normal", "lyrics": "yes", "context": "alone", "distraction": "medium"},
    "reading": {"mind_speed": "slow", "lyrics": "no", "context": "alone", "distraction": "low"},
    "gaming": {"mind_speed": "racing", "lyrics": "sometimes", "context": "alone", "distraction": "medium"},
    "date night": {"mind_speed": "slow", "lyrics": "yes", "context": "with people", "distraction": "medium"},
    "romantic": {"mind_speed": "slow", "lyrics": "yes", "context": "with people", "distraction": "low"},
    "sad": {"mind_speed": "slow", "lyrics": "yes", "context": "alone", "distraction": "low"},
    "happy": {"mind_speed": "normal", "lyrics": "yes", "context": "with people", "distraction": "high"},
    "angry": {"mind_speed": "racing", "lyrics": "yes", "context": "alone", "distraction": "high"},
    "chill": {"mind_speed": "slow", "lyrics": "sometimes", "context": "alone", "distraction": "low"},
}


def find_keyword_match(text: str, keyword_map: dict) -> str:
    """Find the best matching category based on keywords"""
    text_lower = text.lower()
    
    best_match = None
    best_count = 0
    
    for category, keywords in keyword_map.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_match = category
    
    return best_match


def parse_natural_language(text: str) -> dict:
    """
    Parse natural language input and extract mood parameters
    Returns a dictionary with mind_speed, lyrics, context, distraction
    """
    text_lower = text.lower().strip()
    
    # Check for activity presets first
    for activity, preset in ACTIVITY_PRESETS.items():
        if activity in text_lower:
            return {
                "success": True,
                "parsed": preset,
                "matched_activity": activity,
                "message": f"Found activity: {activity}"
            }
    
    # Try to parse individual components
    parsed = {
        "mind_speed": find_keyword_match(text, MOOD_KEYWORDS) or "normal",
        "lyrics": find_keyword_match(text, LYRICS_KEYWORDS) or "sometimes",
        "context": find_keyword_match(text, CONTEXT_KEYWORDS) or "alone",
        "distraction": find_keyword_match(text, DISTRACTION_KEYWORDS) or "medium"
    }
    
    return {
        "success": True,
        "parsed": parsed,
        "matched_activity": None,
        "message": "Parsed from keywords"
    }


def get_activity_suggestions() -> list:
    """Return list of available activity presets"""
    return list(ACTIVITY_PRESETS.keys())


def parse_music_request(text: str) -> str:
    """Legacy function - kept for backwards compatibility"""
    return text.lower()
