from __future__ import annotations
import json
from typing import Dict, Any
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate

from src.music_agent.state import AppState, AgentLog


def _get_llm():
    return ChatMistralAI(
        model="open-mistral-7b",
        temperature=0.7,
        max_tokens=500
    )


def refiner_agent(state: AppState, user_feedback: str) -> AppState:
    current_songs_summary = []
    for song in state["final_playlist"][:5]:
        current_songs_summary.append({
            "name": song.name,
            "artist": song.artist,
            "genres": song.genres[:2],
            "mood": song.mood,
            "energy": song.energy
        })
    
    prompt_template = PromptTemplate.from_template(
        """Analyze this playlist refinement request:

Original Query: {original_query}
Current Playlist: {current_songs}
User Feedback: {feedback}
User Preferences: {preferences}

Determine:
1. What aspects to change (energy, genre, mood, artists)
2. Which songs to remove (if any)
3. What characteristics to emphasize
4. Specific adjustments (numeric ranges for energy, valence, etc)

Return structured modifications in JSON."""
    )
    
    prompt = prompt_template.format(
        original_query=state["query"],
        current_songs=json.dumps(current_songs_summary, indent=2),
        feedback=user_feedback,
        preferences=f"Novelty: {state['preferences'].novelty_tolerance}, Genres: {state['preferences'].genres}"
    )
    
    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        
        analysis = response.content
        
        modifications = {}
        if "more energy" in user_feedback.lower() or "energetic" in user_feedback.lower():
            modifications["energy_adjustment"] = 0.2
        elif "calmer" in user_feedback.lower() or "chill" in user_feedback.lower():
            modifications["energy_adjustment"] = -0.2
            
        if "more novel" in user_feedback.lower() or "different" in user_feedback.lower():
            modifications["novelty_adjustment"] = 0.2
        elif "familiar" in user_feedback.lower():
            modifications["novelty_adjustment"] = -0.2
            
        if "remove" in user_feedback.lower() or "skip" in user_feedback.lower():
            modifications["remove_similar"] = True
            
        state["logs"].append(AgentLog(
            agent_name="Refiner",
            action="analyzed",
            details=f"Feedback: {user_feedback[:50]}... | Adjustments: {modifications}"
        ))
        
        return state, modifications, analysis
        
    except Exception as e:
        state["logs"].append(AgentLog(
            agent_name="Refiner",
            action="error",
            details=f"Failed to parse feedback: {str(e)}"
        ))
        return state, {}, f"Error analyzing feedback: {str(e)}"


def namer_agent(state: AppState) -> tuple[str, str]:
    songs_summary = ", ".join([f"{s.name} by {s.artist}" for s in state["final_playlist"][:5]])
    if len(state["final_playlist"]) > 5:
        songs_summary += f" and {len(state['final_playlist']) - 5} more"
    
    mood = "varied"
    if state.get("session_context") and hasattr(state["session_context"], "mood"):
        mood = state["session_context"].mood or "varied"
    
    prompt_template = PromptTemplate.from_template(
        """Create an awesome playlist title and description:

Songs: {songs}
Original Query: {query}
Vibe: {mood}

Generate:
- A catchy, creative title (3-6 words)
- A one-sentence description that captures the essence
- Make it memorable and shareable

Examples:
- "Midnight Study Vibes: Lo-Fi Beats for Deep Focus"
- "Thunder & Lightning: High-Octane Workout Anthems"
- "Sunset Boulevard: Indie Gems for Golden Hour"

Your turn!"""
    )
    
    prompt = prompt_template.format(
        songs=songs_summary,
        query=state["query"],
        mood=mood
    )
    
    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        
        content = response.content.strip()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        title = "My Playlist"
        description = "A curated selection of tracks"
        
        for line in lines:
            if any(word in line.lower() for word in ["title:", "name:", "playlist:"]):
                title = line.split(":", 1)[-1].strip().strip('"').strip("'")
            elif any(word in line.lower() for word in ["description:", "desc:"]):
                description = line.split(":", 1)[-1].strip().strip('"').strip("'")
        
        if title == "My Playlist" and len(lines) > 0:
            title = lines[0].strip('"').strip("'")
        if description == "A curated selection of tracks" and len(lines) > 1:
            description = lines[1].strip('"').strip("'")
        
        state["logs"].append(AgentLog(
            agent_name="Namer",
            action="generated",
            details=f"Title: {title[:30]}..."
        ))
        
        return title, description
        
    except Exception as e:
        state["logs"].append(AgentLog(
            agent_name="Namer",
            action="error",
            details=f"Failed to generate name: {str(e)}"
        ))
        return "My Playlist", "A curated selection of tracks"
