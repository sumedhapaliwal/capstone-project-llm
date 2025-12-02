from __future__ import annotations
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.music_agent.state import AppState, AgentLog

load_dotenv()


def _get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your-mistral-api-key":
        raise ValueError("MISTRAL_API_KEY not set")
    model = os.getenv("DEFAULT_MODEL", "mistral:open-mistral-7b").split(":", 1)[1]
    return ChatMistralAI(api_key=api_key, model=model, temperature=0.7)


def explanation_agent(state: AppState) -> AppState:
    """Explanation Agent: Creates engaging human-friendly explanations"""
    
    if not state["final_playlist"]:
        state["explanations"].append("No playlist was created.")
        return state
    
    try:
        taste_songs = []
        novel_songs = []
        for candidate in state["candidate_tracks"]:
            if candidate.song in state["final_playlist"]:
                if candidate.source_agent == "taste_recommender":
                    taste_songs.append(candidate.song)
                elif candidate.source_agent == "explorer":
                    novel_songs.append(candidate.song)
        
        all_artists = list(set([s.artist for s in state["final_playlist"]]))
        all_genres = list(set([g for s in state["final_playlist"] for g in s.genres]))
        
        playlist_details = f"ACTUAL PLAYLIST ({len(state['final_playlist'])} tracks):\n"
        for i, song in enumerate(state["final_playlist"], 1):
            source = "familiar" if any(c.song.id == song.id and c.source_agent == "taste_recommender" for c in state["candidate_tracks"]) else "new"
            playlist_details += f"{i}. {song.name} by {song.artist} [{', '.join(song.genres[:2])}] - {source}\n"
        
        llm = _get_llm()
        
        prompt = f"""Create a fun explanation for this music playlist based on ACTUAL songs.

User asked: "{state['query']}"
Activity: {state['session_context'].activity or 'casual listening'}

{playlist_details}

Artists: {', '.join(all_artists[:5])}
Genres: {', '.join(all_genres[:5])}

IMPORTANT: Base your explanation on the ACTUAL songs listed above. Don't invent artists or genres not in the list.

Write 2-3 sentences that:
1. Mention the REAL artists and genres from the playlist
2. Explain the mix (familiar vs new artists)
3. Make it sound exciting but HONEST

Be casual and accurate."""
        
        messages = [
            SystemMessage(content="You are a music curator explaining playlists to friends."),
            HumanMessage(content=prompt)
        ]
        
        resp = llm.invoke(messages)
        explanation = resp.content.strip()
        
        state["explanations"].append(explanation)
        
        state["logs"].append(AgentLog(
            agent_name="Storyteller",
            action="explained",
            details=f"Generated user-friendly explanation ({len(explanation)} chars)"
        ))
        
    except Exception as e:
        artists = list(set([s.artist for s in state["final_playlist"]]))[:5]
        genres = list(set([g for s in state["final_playlist"] for g in s.genres]))[:5]
        
        taste_count = len([c for c in state["candidate_tracks"] if c.song in state["final_playlist"] and c.source_agent == "taste_recommender"])
        novel_count = len([c for c in state["candidate_tracks"] if c.song in state["final_playlist"] and c.source_agent == "explorer"])
        
        explanation = f"Created a {len(state['final_playlist'])}-track playlist "
        explanation += f"featuring {', '.join(artists[:3])}{'and more' if len(artists) > 3 else ''}. "
        explanation += f"Mix of {genres[0]} and {genres[1]} with " if len(genres) >= 2 else ""
        explanation += f"{taste_count} familiar tracks and {novel_count} new discoveries."
        
        state["explanations"].append(explanation)
        
        state["logs"].append(AgentLog(
            agent_name="Storyteller",
            action="fallback_explanation",
            details=f"Used template explanation: {str(e)}"
        ))
    
    return state


def generate_song_explanation(song, state: AppState) -> str:
    """Generate explanation for why a specific song was chosen"""
    
    candidate = None
    for c in state["candidate_tracks"]:
        if c.song.id == song.id:
            candidate = c
            break
    
    if candidate:
        return candidate.reason
    
    return f"This track matches your vibe with its {', '.join(song.genres[:2])} energy."
