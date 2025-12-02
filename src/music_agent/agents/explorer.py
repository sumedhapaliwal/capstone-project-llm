from __future__ import annotations
from typing import List
import random

from src.music_agent.state import AppState, CandidateTrack, Song, AgentLog


def calculate_novelty(song: Song, user_memory: dict) -> float:
    """Calculate how novel/unfamiliar a song is"""
    novelty = 1.0
    
    if song.artist in user_memory.get("preferred_artists", []):
        novelty -= 0.5
    
    known_genres = user_memory.get("preferred_genres", [])
    if known_genres:
        genre_overlap = len(set(song.genres) & set(known_genres))
        novelty -= (genre_overlap / len(known_genres)) * 0.3
    
    if song.popularity:
        if song.popularity < 50:
            novelty += 0.2
    
    return max(0.0, min(1.0, novelty))


def explorer_agent(state: AppState) -> AppState:
    """Explorer Agent: Pushes user out of comfort zone with novel recommendations"""
    
    from src.music_agent.agents.memory import load_user_memory
    
    user_memory = load_user_memory(state["user_id"])
    excluded_ids = set(user_memory.get("disliked_songs", []))
    known_artists = set(user_memory.get("preferred_artists", []))
    
    novel_candidates = []
    for song in state["library"]:
        if song.id in excluded_ids:
            continue
        
        if song.artist in known_artists:
            continue
        
        novelty = calculate_novelty(song, user_memory)
        
        if novelty > 0.5:
            exploration_score = novelty
            
            for genre in song.genres:
                if any(ug in genre or genre in ug for ug in user_memory.get("preferred_genres", [])):
                    exploration_score += 0.3
                    break
            
            if state["session_context"] and state["session_context"].activity:
                activity = state["session_context"].activity.lower()
                if activity == "studying" or activity == "work":
                    if song.energy and song.energy < 0.5:
                        exploration_score += 1.0
                    elif song.energy and song.energy > 0.7:
                        exploration_score -= 0.5
                        
                elif activity == "party" or activity == "dancing":
                    if song.energy and song.energy > 0.7:
                        exploration_score += 1.0
                    if song.danceability and song.danceability > 0.6:
                        exploration_score += 0.5
                    elif song.energy and song.energy < 0.4:
                        exploration_score -= 0.5
                        
                elif activity == "gym" or activity == "workout":
                    if song.energy and song.energy > 0.8:
                        exploration_score += 1.5
                    elif song.energy and song.energy < 0.5:
                        exploration_score -= 1.0
            
            if state["session_context"] and state["session_context"].mood:
                mood = state["session_context"].mood.lower()
                if mood == "calm" and song.energy and song.energy < 0.4:
                    exploration_score += 0.8
                elif mood == "energetic" and song.energy and song.energy > 0.7:
                    exploration_score += 0.8
                elif mood == "happy" and song.valence and song.valence > 0.6:
                    exploration_score += 0.5
                elif mood == "sad" and song.valence and song.valence < 0.4:
                    exploration_score += 0.5
            
            if state["session_context"].activity:
                activity = state["session_context"].activity.lower()
                if "gym" in activity or "workout" in activity:
                    if song.energy and song.energy > 0.7:
                        exploration_score += 0.5
                elif "chill" in activity or "relax" in activity:
                    if song.energy and song.energy < 0.4:
                        exploration_score += 0.5
            
            reason = f"New artist '{song.artist}' with similar energy to your taste"
            if state["session_context"] and state["session_context"].activity:
                activity = state["session_context"].activity
                if activity == "studying":
                    reason = f"Unknown calm artist '{song.artist}' perfect for studying"
                elif activity == "party":
                    reason = f"Energetic new artist '{song.artist}' great for parties"
                elif activity == "gym":
                    reason = f"High-energy unknown artist '{song.artist}' for workouts"
            
            novel_candidates.append(CandidateTrack(
                song=song,
                score=exploration_score,
                source_agent="explorer",
                reason=reason,
                novelty_score=novelty,
                confidence=0.6
            ))
    
    novel_candidates.sort(key=lambda x: x.score, reverse=True)
    
    num_novel = int(state["preferences"].size * state["preferences"].novelty_tolerance)
    num_novel = max(1, num_novel)
    
    top_novel = novel_candidates[:num_novel * 2]
    
    existing_song_ids = {c.song.id for c in state["candidate_tracks"]}
    unique_novel = [c for c in top_novel if c.song.id not in existing_song_ids]
    
    state["candidate_tracks"].extend(unique_novel)
    
    activity_context = state["session_context"].activity if state["session_context"] else "general"
    state["logs"].append(AgentLog(
        agent_name="Chaos DJ",
        action="explored",
        details=f"Added {len(unique_novel)} novel tracks for {activity_context} from new artists"
    ))
    
    return state
