from __future__ import annotations
import json
from pathlib import Path
from src.music_agent.state import AppState, UserPreferences, AgentLog


USER_PREFS_FILE = Path(__file__).parents[1] / "data" / "user_prefs.json"


def load_user_memory(user_id: str) -> dict:
    """Load user's long-term memory"""
    if USER_PREFS_FILE.exists():
        with open(USER_PREFS_FILE, "r") as f:
            return json.load(f)
    return {
        "liked_songs": [],
        "disliked_songs": [],
        "preferred_genres": [],
        "preferred_moods": [],
        "preferred_artists": [],
        "listening_history": []
    }


def save_user_memory(user_id: str, memory: dict):
    """Save user's long-term memory"""
    with open(USER_PREFS_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def memory_agent(state: AppState) -> AppState:
    """Memory Agent: Manages user profile and persistent preferences"""
    
    user_memory = load_user_memory(state["user_id"])
    
    if user_memory["preferred_genres"] and not state["preferences"].genres:
        state["preferences"].genres = user_memory["preferred_genres"][:5]
    
    if user_memory["preferred_moods"] and not state["preferences"].moods:
        state["preferences"].moods = user_memory["preferred_moods"][:3]
    
    if user_memory["preferred_artists"] and not state["preferences"].artists:
        state["preferences"].artists = user_memory["preferred_artists"][:5]
    
    details = []
    if user_memory["preferred_genres"]:
        details.append(f"Genres: {', '.join(user_memory['preferred_genres'][:3])}")
    if user_memory["preferred_artists"]:
        details.append(f"Artists: {', '.join(user_memory['preferred_artists'][:3])}")
    
    state["logs"].append(AgentLog(
        agent_name="Memory Agent",
        action="loaded_profile",
        details="; ".join(details) if details else "No prior history"
    ))
    
    return state


def update_user_memory(user_id: str, feedback: dict):
    """Update user memory based on feedback"""
    memory = load_user_memory(user_id)
    
    if "liked_song" in feedback:
        song = feedback["liked_song"]
        if song["id"] not in memory["liked_songs"]:
            memory["liked_songs"].append(song["id"])
        
        for genre in song.get("genres", []):
            if genre not in memory["preferred_genres"]:
                memory["preferred_genres"].append(genre)
        
        if song.get("mood") and song["mood"] not in memory["preferred_moods"]:
            memory["preferred_moods"].append(song["mood"])
        
        if song.get("artist") and song["artist"] not in memory["preferred_artists"]:
            memory["preferred_artists"].append(song["artist"])
    
    if "disliked_song" in feedback:
        song_id = feedback["disliked_song"]["id"]
        if song_id not in memory["disliked_songs"]:
            memory["disliked_songs"].append(song_id)
    
    save_user_memory(user_id, memory)
