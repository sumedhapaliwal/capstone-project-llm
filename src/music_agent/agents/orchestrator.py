from __future__ import annotations
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

from src.music_agent.state import AppState, Intent, UserPreferences, SessionContext, AgentLog

load_dotenv()


def _get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your-mistral-api-key":
        raise ValueError("MISTRAL_API_KEY not set")
    model = os.getenv("DEFAULT_MODEL", "mistral:open-mistral-7b").split(":", 1)[1]
    return ChatMistralAI(api_key=api_key, model=model, temperature=0.2)


SYSTEM_PROMPT = """You are the Orchestrator Agent - the brain of a music intelligence system.

Analyze the user's request and extract:
1. Intent: recommend, explain, update_prefs, surprise_me
2. Session context: activity, duration, mood
3. Preferences: genres, artists, languages, explicit filter, novelty tolerance

Return ONLY valid JSON:
{
    "intent": "recommend",
    "session_context": {
        "activity": "gym",
        "duration_minutes": 40,
        "mood": "energetic"
    },
    "preferences": {
        "query": "40-minute gym playlist, mostly Hindi rap, surprise me with 3 new artists",
        "genres": ["rap", "hip-hop"],
        "language_prefs": ["hindi"],
        "size": 10,
        "novelty_tolerance": 0.3
    }
}"""


def parse_query_heuristically(query: str) -> dict:
    """Fallback heuristic parser when LLM is unavailable"""
    query_lower = query.lower()
    
    activity = None
    if any(word in query_lower for word in ["study", "studying", "homework", "reading"]):
        activity = "studying"
    elif any(word in query_lower for word in ["party", "dance", "club", "dancing"]):
        activity = "party"
    elif any(word in query_lower for word in ["gym", "workout", "exercise", "running"]):
        activity = "gym"
    elif any(word in query_lower for word in ["sleep", "bedtime", "night", "ambient"]):
        activity = "sleep"
    elif any(word in query_lower for word in ["work", "focus", "concentration"]):
        activity = "work"
    
    mood = None
    if any(word in query_lower for word in ["calm", "chill", "relaxing", "peaceful", "quiet"]):
        mood = "calm"
    elif any(word in query_lower for word in ["energetic", "energy", "high-energy", "upbeat", "pump"]):
        mood = "energetic"
    elif any(word in query_lower for word in ["happy", "cheerful", "positive", "uplifting"]):
        mood = "happy"
    elif any(word in query_lower for word in ["sad", "melancholy", "emotional", "heartbreak"]):
        mood = "sad"
    
    genres = []
    genre_keywords = {
        "pop": ["pop", "mainstream"],
        "rock": ["rock", "alternative"],
        "hip-hop": ["hip-hop", "rap", "hiphop"],
        "electronic": ["electronic", "edm", "techno", "house", "dance"],
        "indie": ["indie", "independent"],
        "jazz": ["jazz"],
        "classical": ["classical", "orchestra"],
        "r&b": ["r&b", "rnb", "soul"],
        "country": ["country"],
        "folk": ["folk", "acoustic"]
    }
    
    for genre, keywords in genre_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            genres.append(genre)
    
    moods = []
    if mood:
        moods.append(mood)
    
    return {
        "intent": "recommend",
        "session_context": {
            "activity": activity,
            "mood": mood
        },
        "preferences": {
            "query": query,
            "genres": genres,
            "moods": moods,
            "size": 10,
            "novelty_tolerance": 0.3
        }
    }


def orchestrator_agent(state: AppState) -> AppState:
    """Orchestrator Agent: Interprets user query and sets up the workflow"""
    try:
        llm = _get_llm()
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"User request: {state['query']}")
        ]
        
        resp = llm.invoke(messages)
        content = resp.content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        data = json.loads(content)
        
        state["intent"] = data.get("intent", "recommend")
        
        session_ctx = data.get("session_context", {})
        state["session_context"] = SessionContext(**session_ctx)
        
        prefs_data = data.get("preferences", {})
        prefs_data.setdefault("query", state["query"])
        prefs_data.setdefault("size", 10)
        state["preferences"] = UserPreferences(**prefs_data)
        
        state["logs"].append(AgentLog(
            agent_name="Orchestrator",
            action="parsed_intent",
            details=f"Intent: {state['intent']}, Activity: {session_ctx.get('activity', 'N/A')}, Size: {prefs_data.get('size', 10)}"
        ))
        
    except Exception as e:
        data = parse_query_heuristically(state["query"])
        
        state["intent"] = data.get("intent", "recommend")
        
        session_ctx = data.get("session_context", {})
        state["session_context"] = SessionContext(**session_ctx)
        
        prefs_data = data.get("preferences", {})
        prefs_data.setdefault("query", state["query"])
        prefs_data.setdefault("size", 10)
        state["preferences"] = UserPreferences(**prefs_data)
        
        state["logs"].append(AgentLog(
            agent_name="Orchestrator",
            action="heuristic_fallback",
            details=f"LLM unavailable, used heuristics: Activity={session_ctx.get('activity', 'None')}, Mood={session_ctx.get('mood', 'None')}, Genres={prefs_data.get('genres', [])}"
        ))
    
    return state
