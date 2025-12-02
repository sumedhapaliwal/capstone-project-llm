from __future__ import annotations
from typing import Dict
import json
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.music_agent.state import Intent, UserPreferences

load_dotenv()

def _get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key == "your-mistral-api-key":
        raise ValueError(
            "MISTRAL_API_KEY not set or invalid. "
            "Get your key from https://console.mistral.ai/ and set it in .env or Streamlit sidebar."
        )
    model = os.getenv("DEFAULT_MODEL", "mistral:open-mistral-7b").split(":", 1)[1]
    return ChatMistralAI(api_key=api_key, model=model, temperature=0.2)


SYSTEM = (
    "You are an intent parser for a Music Intelligence Terminal. "
    "Parse the user's request into a strict JSON with keys: action, preferences. "
    "action in {search, recommend, playlist_create, playlist_expand, analyze}. "
    "preferences fields: query (str|optional), genres (list[str]), artists (list[str]), "
    "tags (list[str]), moods (list[str]), min_year (int|null), max_year (int|null), size (int). "
    "Return ONLY JSON."
)


def parse_intent(nl_query: str) -> Intent:
    try:
        llm = _get_llm()
        messages = [
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"User request: {nl_query}\nReturn JSON only.")
        ]
        resp = llm.invoke(messages)
        
        try:
            content = resp.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            data: Dict = json.loads(content)
        except json.JSONDecodeError as e:
            data = {"action": "recommend", "preferences": {"query": nl_query, "size": 10}}
        
        prefs = data.get("preferences", {})
        prefs.setdefault("genres", [])
        prefs.setdefault("artists", [])
        prefs.setdefault("tags", [])
        prefs.setdefault("moods", [])
        prefs.setdefault("size", 10)
        prefs.setdefault("query", nl_query)
        return Intent(action=data.get("action", "recommend"), preferences=UserPreferences(**prefs))
    
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "capacity exceeded" in error_msg.lower():
            raise RuntimeError(
                "Mistral AI rate limit exceeded. Please wait a moment and try again, "
                "or check your API plan at https://console.mistral.ai/"
            )
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            raise RuntimeError(
                "Invalid Mistral API key. Please check your API key in the sidebar or .env file."
            )
        else:
            raise RuntimeError(f"AI service error: {error_msg}")


def summarize_playlist(title: str, songs: list[dict]) -> str:
    try:
        llm = _get_llm()
        summary_sys = (
            "You are a music curator. Given a playlist title and songs (name, artist, tags, mood), "
            "write a 2-3 sentence engaging summary."
        )
        txt = "\n".join([f"- {s['name']} by {s['artist']} [{', '.join(s.get('tags', []))}] mood={s.get('mood','') }" for s in songs])
        messages = [
            SystemMessage(content=summary_sys),
            HumanMessage(content=f"Title: {title}\nSongs:\n{txt}")
        ]
        resp = llm.invoke(messages)
        return resp.content.strip()
    except Exception as e:
        artists = list(set([s['artist'] for s in songs[:5]]))
        return f"A collection of {len(songs)} tracks featuring {', '.join(artists[:3])}{'and more' if len(artists) > 3 else ''}."
