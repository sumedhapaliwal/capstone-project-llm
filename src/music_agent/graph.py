from __future__ import annotations
from typing import Callable

from langgraph.graph import StateGraph, END

from src.music_agent.state import AgentState, Playlist
from src.music_agent.tools.library import load_default_library
from src.music_agent.tools.recommend import recommend_by_prefs
from src.music_agent.agents.planner import parse_intent, summarize_playlist


def build_graph() -> tuple[StateGraph, Callable[[dict], dict]]:
    lib = load_default_library()

    def initialize(state: AgentState) -> AgentState:
        state["library"] = lib.songs
        state["candidate_songs"] = []
        state["playlist"] = None
        state["error"] = None
        return state

    def plan(state: AgentState) -> AgentState:
        try:
            q = state["preferences"].query or "recommend upbeat pop for a workout, 10 songs"
            intent = parse_intent(q)
            state["last_action"] = intent.action
            state["preferences"] = intent.preferences
        except Exception as e:
            state["error"] = f"Intent parse failed: {e}"
        return state

    def retrieve_or_recommend(state: AgentState) -> AgentState:
        try:
            k = state["preferences"].size
            cands = recommend_by_prefs(load_default_library(), state["preferences"], k * 3)
            state["candidate_songs"] = cands
        except Exception as e:
            state["error"] = f"Recommend failed: {e}"
        return state

    def compose_playlist(state: AgentState) -> AgentState:
        try:
            size = state["preferences"].size
            picks = state["candidate_songs"][:size]
            title = state["preferences"].query or "Your Personalized Playlist"
            pl = Playlist(title=title, songs=picks, description=None)
            pl.description = summarize_playlist(title, [s.model_dump() for s in picks])
            state["playlist"] = pl
        except Exception as e:
            state["error"] = f"Compose failed: {e}"
        return state

    def done(state: AgentState) -> AgentState:
        return state

    sg = StateGraph(AgentState)
    sg.add_node("initialize", initialize)
    sg.add_node("plan", plan)
    sg.add_node("recommend", retrieve_or_recommend)
    sg.add_node("compose", compose_playlist)
    sg.add_node("done", done)

    sg.set_entry_point("initialize")
    sg.add_edge("initialize", "plan")
    sg.add_edge("plan", "recommend")
    sg.add_edge("recommend", "compose")
    sg.add_edge("compose", "done")
    sg.add_edge("done", END)

    app = sg.compile()
    return app, lib
