from __future__ import annotations
from typing import List
import numpy as np

from src.music_agent.state import AppState, CandidateTrack, Song, AgentLog


def score_song_taste(song: Song, prefs, user_memory: dict, session_context) -> float:
    """Score song based on user's established taste and session context"""
    score = 0.0
    
    for genre in prefs.genres:
        if genre.lower() in [g.lower() for g in song.genres]:
            score += 1.5
    
    if song.artist in user_memory.get("preferred_artists", []):
        score += 2.0
    
    if prefs.moods and song.mood in prefs.moods:
        score += 1.0
    
    if session_context and session_context.activity:
        activity = session_context.activity.lower()
        if activity == "studying" or activity == "work":
            if song.energy and song.energy < 0.5:
                score += 1.5
            elif song.energy and song.energy > 0.7:
                score -= 1.0
            if any(tag in song.tags for tag in ["instrumental", "ambient", "acoustic"]):
                score += 1.0
                
        elif activity == "party" or activity == "dancing":
            if song.energy and song.energy > 0.7:
                score += 1.5
            if song.danceability and song.danceability > 0.6:
                score += 1.0
            elif song.energy and song.energy < 0.4:
                score -= 1.0
                
        elif activity == "gym" or activity == "workout":
            if song.energy and song.energy > 0.8:
                score += 2.0
            elif song.energy and song.energy < 0.5:
                score -= 1.5
    
    if session_context and session_context.mood:
        mood = session_context.mood.lower()
        if mood == "calm" and song.energy and song.energy < 0.4:
            score += 1.5
        elif mood == "energetic" and song.energy and song.energy > 0.7:
            score += 1.5
        elif mood == "happy" and song.valence and song.valence > 0.6:
            score += 1.0
        elif mood == "sad" and song.valence and song.valence < 0.4:
            score += 1.0
    
    for tag in prefs.tags:
        if tag in song.tags:
            score += 0.8
    
    if prefs.min_year and song.year and song.year >= prefs.min_year:
        score += 0.3
    if prefs.max_year and song.year and song.year <= prefs.max_year:
        score += 0.3
    
    if song.popularity:
        score += (song.popularity / 100.0) * 0.5
    
    if song.energy and prefs.moods:
        if "energetic" in [m.lower() for m in prefs.moods] and song.energy > 0.7:
            score += 0.5
        elif "calm" in [m.lower() for m in prefs.moods] and song.energy < 0.4:
            score += 0.5
    
    return score


def taste_recommender_agent(state: AppState) -> AppState:
    """Taste-Based Recommender Agent: Safe bets that match user preferences"""
    
    from src.music_agent.agents.memory import load_user_memory
    
    user_memory = load_user_memory(state["user_id"])
    excluded_ids = set(user_memory.get("disliked_songs", []))
    
    candidates = []
    for song in state["library"]:
        if song.id in excluded_ids:
            continue
        
        score = score_song_taste(song, state["preferences"], user_memory, state["session_context"])
        
        if score > 0.5:
            reason = f"Matches your taste in {', '.join(song.genres[:2])}"
            if state["session_context"] and state["session_context"].activity:
                activity = state["session_context"].activity
                if activity == "studying":
                    reason = f"Perfect for {activity} - calm {', '.join(song.genres[:2])}"
                elif activity == "party":
                    reason = f"Great for {activity} - energetic {', '.join(song.genres[:2])}"
                else:
                    reason = f"Ideal for {activity} - {', '.join(song.genres[:2])}"
            
            candidates.append(CandidateTrack(
                song=song,
                score=score,
                source_agent="taste_recommender",
                reason=reason,
                novelty_score=0.1,
                confidence=0.9
            ))
    
    candidates.sort(key=lambda x: x.score, reverse=True)
    top_candidates = candidates[:int(state["preferences"].size * 0.7)]
    
    existing_song_ids = {c.song.id for c in state["candidate_tracks"]}
    unique_candidates = [c for c in top_candidates if c.song.id not in existing_song_ids]
    
    state["candidate_tracks"].extend(unique_candidates)
    
    activity_context = state["session_context"].activity if state["session_context"] else "general"
    state["logs"].append(AgentLog(
        agent_name="Taste DJ",
        action="recommended",
        details=f"Added {len(unique_candidates)} tracks for {activity_context} based on your taste profile"
    ))
    
    return state
