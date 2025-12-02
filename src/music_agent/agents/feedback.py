from __future__ import annotations
from src.music_agent.state import AppState, AgentLog
from src.music_agent.agents.memory import update_user_memory


def feedback_agent(state: AppState) -> AppState:
    """Feedback Agent: Processes user feedback and updates learning"""
    
    if not state.get("feedback"):
        return state
    
    feedback = state["feedback"]
    
    # update user memory based on feedback
    update_user_memory(state["user_id"], feedback)
    
    feedback_type = "liked" if "liked_song" in feedback else "disliked"
    song_name = feedback.get("liked_song", feedback.get("disliked_song", {})).get("name", "unknown")
    
    state["logs"].append(AgentLog(
        agent_name="Feedback Agent",
        action="processed_feedback",
        details=f"User {feedback_type} '{song_name}', updated taste profile"
    ))
    
    # adjust novelty tolerance based on feedback patterns
    if "adjust_novelty" in feedback:
        current_tolerance = state["preferences"].novelty_tolerance
        adjustment = feedback["adjust_novelty"]
        
        new_tolerance = max(0.0, min(1.0, current_tolerance + adjustment))
        state["preferences"].novelty_tolerance = new_tolerance
        
        state["logs"].append(AgentLog(
            agent_name="Feedback Agent",
            action="adjusted_novelty",
            details=f"Novelty tolerance: {current_tolerance:.2f} -> {new_tolerance:.2f}"
        ))
    
    return state
