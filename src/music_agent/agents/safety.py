from __future__ import annotations
from typing import List

from src.music_agent.state import AppState, CandidateTrack, Song, AgentLog


def check_content_policy(song: Song, prefs) -> tuple[bool, str]:
    """Check if song passes content policies"""
    
    if prefs.language_prefs:
        pass
    
    if prefs.explicit_filter:
        if "explicit" in [t.lower() for t in song.tags]:
            return False, "Explicit content filtered"
    
    return True, ""


def safety_agent(state: AppState) -> AppState:
    """Safety Agent: Enforces content rules and guardrails"""
    
    filtered_candidates = []
    filtered_count = 0
    filter_reasons = []
    
    for candidate in state["candidate_tracks"]:
        passed, reason = check_content_policy(candidate.song, state["preferences"])
        
        if passed:
            filtered_candidates.append(candidate)
        else:
            filtered_count += 1
            if reason not in filter_reasons:
                filter_reasons.append(reason)
    
    state["candidate_tracks"] = filtered_candidates
    
    details = f"Checked {len(state['candidate_tracks']) + filtered_count} tracks"
    if filtered_count > 0:
        details += f", filtered {filtered_count} ({', '.join(filter_reasons)})"
    else:
        details += ", all passed policy checks"
    
    state["logs"].append(AgentLog(
        agent_name="Safety Agent",
        action="filtered",
        details=details
    ))
    
    return state
