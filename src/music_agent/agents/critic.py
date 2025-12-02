from __future__ import annotations
from typing import List
import numpy as np

from src.music_agent.state import AppState, CandidateTrack, Song, AgentLog


def multi_objective_score(candidate: CandidateTrack, state: AppState) -> float:
    """Calculate final score using multiple objectives"""
    
    score = candidate.score
    
    intent = state["intent"]
    if intent == "recommend":
        familiarity_weight = 1.0 - state["preferences"].novelty_tolerance
        novelty_weight = state["preferences"].novelty_tolerance
        
        if candidate.source_agent == "taste_recommender":
            score *= (0.7 + 0.3 * familiarity_weight)
        elif candidate.source_agent == "explorer":
            score *= (0.5 + 0.5 * novelty_weight)
    
    score *= candidate.confidence
    
    ctx = state["session_context"]
    song = candidate.song
    
    if ctx.activity:
        activity = ctx.activity.lower()
        if "gym" in activity or "workout" in activity:
            if song.energy and song.energy > 0.7:
                score *= 1.3
            elif song.energy and song.energy < 0.4:
                score *= 0.6
        elif "chill" in activity or "study" in activity:
            if song.energy and song.energy < 0.4:
                score *= 1.2
    
    if ctx.mood:
        mood = ctx.mood.lower()
        if song.mood and mood in song.mood.lower():
            score *= 1.2
    
    return score


def critic_agent(state: AppState) -> AppState:
    """Critic Agent: Reranks and curates final playlist"""
    
    for candidate in state["candidate_tracks"]:
        candidate.score = multi_objective_score(candidate, state)
    
    state["candidate_tracks"].sort(key=lambda x: x.score, reverse=True)
    
    final_songs = []
    seen_artists = set()
    seen_song_ids = set()
    target_size = state["preferences"].size
    
    for candidate in state["candidate_tracks"]:
        if len(final_songs) >= target_size:
            break
        
        if candidate.song.id in seen_song_ids:
            continue
            
        if candidate.song.artist not in seen_artists or len(seen_artists) < 3:
            final_songs.append(candidate.song)
            seen_artists.add(candidate.song.artist)
            seen_song_ids.add(candidate.song.id)
    
    if len(final_songs) < target_size:
        for candidate in state["candidate_tracks"]:
            if len(final_songs) >= target_size:
                break
            if candidate.song.id not in seen_song_ids:
                final_songs.append(candidate.song)
                seen_song_ids.add(candidate.song.id)
    
    state["final_playlist"] = final_songs[:target_size]
    
    taste_count = sum(1 for c in state["candidate_tracks"][:target_size] if c.source_agent == "taste_recommender")
    novel_count = sum(1 for c in state["candidate_tracks"][:target_size] if c.source_agent == "explorer")
    
    state["logs"].append(AgentLog(
        agent_name="Critic",
        action="curated",
        details=f"Final playlist: {len(final_songs)} tracks ({taste_count} familiar, {novel_count} novel)"
    ))
    
    return state
