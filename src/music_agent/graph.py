from __future__ import annotations
from typing import Literal
import uuid

from langgraph.graph import StateGraph, END

from src.music_agent.state import AppState, UserPreferences, SessionContext
from src.music_agent.tools.library import load_default_library
from src.music_agent.agents.orchestrator import orchestrator_agent
from src.music_agent.agents.memory import memory_agent
from src.music_agent.agents.taste_recommender import taste_recommender_agent
from src.music_agent.agents.explorer import explorer_agent
from src.music_agent.agents.safety import safety_agent
from src.music_agent.agents.critic import critic_agent
from src.music_agent.agents.explainer import explanation_agent
from src.music_agent.agents.feedback import feedback_agent


def build_multi_agent_graph():
    """Build the multi-agent music intelligence graph"""
    
    lib = load_default_library()
    
    def initialize(state: AppState) -> AppState:
        if "user_id" not in state:
            state["user_id"] = "default_user"
        if "query" not in state:
            state["query"] = "recommend me some songs"
        if "library" not in state:
            state["library"] = lib.songs
        if "candidate_tracks" not in state:
            state["candidate_tracks"] = []
        if "final_playlist" not in state:
            state["final_playlist"] = []
        if "explanations" not in state:
            state["explanations"] = []
        if "logs" not in state:
            state["logs"] = []
        if "error" not in state:
            state["error"] = None
        if "requires_human_review" not in state:
            state["requires_human_review"] = False
        if "feedback" not in state:
            state["feedback"] = None
        
        return state
    
    def route_after_orchestrator(state: AppState) -> Literal["memory", "done"]:
        if state.get("error"):
            return "done"
        return "memory"
    
    def parallel_recommenders(state: AppState) -> AppState:
        state = taste_recommender_agent(state)
        state = explorer_agent(state)
        return state
    
    def route_to_human_review(state: AppState) -> Literal["human_review", "critic"]:
        if state.get("requires_human_review"):
            return "human_review"
        return "critic"
    
    def human_review(state: AppState) -> AppState:
        state["requires_human_review"] = False
        return state
    
    def done(state: AppState) -> AppState:
        return state
    
    workflow = StateGraph(AppState)
    
    workflow.add_node("initialize", initialize)
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("memory", memory_agent)
    workflow.add_node("recommenders", parallel_recommenders)
    workflow.add_node("safety", safety_agent)
    workflow.add_node("critic", critic_agent)
    workflow.add_node("explainer", explanation_agent)
    workflow.add_node("feedback", feedback_agent)
    workflow.add_node("human_review", human_review)
    workflow.add_node("done", done)
    
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "orchestrator")
    workflow.add_conditional_edges("orchestrator", route_after_orchestrator)
    workflow.add_edge("memory", "recommenders")
    workflow.add_edge("recommenders", "safety")
    workflow.add_conditional_edges("safety", route_to_human_review)
    workflow.add_edge("human_review", "critic")
    workflow.add_edge("critic", "explainer")
    workflow.add_edge("explainer", "done")
    workflow.add_edge("done", END)
    
    app = workflow.compile()
    
    return app, lib


def invoke_workflow(query: str, user_id: str = "default_user", **kwargs):
    """Invoke the multi-agent workflow"""
    
    app, lib = build_multi_agent_graph()
    
    initial_state = {
        "user_id": user_id,
        "query": query,
        "library": lib.songs,
        "candidate_tracks": [],
        "final_playlist": [],
        "explanations": [],
        "logs": [],
        "error": None,
        "requires_human_review": False,
        "feedback": None,
        **kwargs
    }
    
    result = app.invoke(initial_state)
    
    return result
