"""
Generate visualization and export graph structure to output folder
"""
from pathlib import Path
import json
from src.music_agent.graph import build_multi_agent_graph

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# build the graph
app, lib = build_multi_agent_graph()

# export graph structure as mermaid diagram
mermaid_diagram = """
# Multi-Agent Music Intelligence System

## Agent Architecture

```mermaid
graph TD
    Start([User Query]) --> Init[Initialize]
    Init --> Orch[🧑‍✈️ Orchestrator<br/>Parse intent & context]
    Orch --> Memory[🧬 Memory Agent<br/>Load user profile]
    
    Memory --> Parallel{Parallel Execution}
    
    Parallel --> Taste[🎯 Taste DJ<br/>Familiar recommendations]
    Parallel --> Explorer[🧪 Chaos DJ<br/>Novel discoveries]
    
    Taste --> Merge[Merge Candidates]
    Explorer --> Merge
    
    Merge --> Safety[🛡️ Safety Agent<br/>Content policy checks]
    
    Safety --> Review{Needs Review?}
    Review -->|Yes| Human[👤 Human Review]
    Review -->|No| Critic[🧑‍⚖️ Critic<br/>Rerank & curate]
    Human --> Critic
    
    Critic --> Explain[🌈 Storyteller<br/>Generate explanation]
    
    Explain --> Done[Final Playlist]
    Done --> End([Return to User])
    
    style Orch fill:#4a90e2
    style Memory fill:#7b68ee
    style Taste fill:#50c878
    style Explorer fill:#ff6b6b
    style Safety fill:#ffd700
    style Critic fill:#ff8c42
    style Explain fill:#9b59b6
```

## Agent Responsibilities

### 🧑‍✈️ Orchestrator Agent
- **Role**: Brain of the system
- **Input**: User query
- **Output**: Parsed intent, session context, preferences
- **Key Actions**:
  - NL → structured intent
  - Extract activity, duration, mood
  - Set workflow parameters

### 🧬 Memory Agent  
- **Role**: Persistent state manager
- **Input**: User ID
- **Output**: Long-term taste profile
- **Maintains**:
  - Liked/disliked songs
  - Preferred genres, artists, moods
  - Listening history
- **Updates**: On every feedback action

### 🎯 Taste DJ (Recommender)
- **Role**: Safe bets that match taste
- **Strategy**: 
  - High weight on known preferences
  - Artist familiarity boost
  - Genre/mood matching
- **Output**: ~70% of playlist (familiar tracks)

### 🧪 Chaos DJ (Explorer)
- **Role**: Push out of comfort zone
- **Strategy**:
  - Filter out known artists
  - Find adjacent genres
  - High novelty scoring
- **Output**: ~30% of playlist (discoveries)

### 🛡️ Safety Agent
- **Role**: Content guardrails
- **Checks**:
  - Explicit content filter
  - Language preferences
  - User-defined rules
- **Authority**: Can drop tracks, log reasons

### 🧑‍⚖️ Critic Agent
- **Role**: Final curator & judge
- **Multi-objective scoring**:
  - Intent alignment
  - Novelty vs familiarity balance
  - Session context matching
  - Artist diversity
- **Output**: Final ranked playlist

### 🌈 Storyteller (Explainer)
- **Role**: Human-friendly explanations
- **Input**: Final playlist + agent logs
- **Output**: Engaging 2-3 sentence summary
- **Capability**: Per-song "why" answers

### 📊 Feedback Agent
- **Role**: Learning & adaptation
- **Triggers**: Like/dislike/skip actions
- **Updates**:
  - User profile
  - Novelty tolerance
  - Genre/artist preferences

## State Flow

```
AppState {
    user_id: str
    query: str
    intent: recommend | explain | update_prefs
    preferences: {genres, artists, moods, size, novelty_tolerance}
    session_context: {activity, duration, mood}
    candidate_tracks: [CandidateTrack]  # from multiple agents
    final_playlist: [Song]
    explanations: [str]
    logs: [AgentLog]  # full trace
    requires_human_review: bool
}
```

## Key Features Demonstrated

### ✅ Multi-Agent Coordination
- Orchestrator routes workflow
- Parallel execution (Taste + Explorer)
- Agent specialization (taste vs novelty)

### ✅ Persistent Memory
- User profile stored across sessions
- Feedback loop updates preferences
- Online learning from interactions

### ✅ Human Oversight
- Optional review node
- Feedback-driven adjustments
- Explainable decisions (full log trace)

### ✅ Advanced LangGraph Features
- TypedDict state with Annotated fields
- Conditional routing (review, error handling)
- Parallel branches (simulated)
- Stateful checkpointing (memory)

### ✅ Tracing & Debuggability
- AgentLog captures every decision
- Per-track reasoning stored
- Graph visualization via mermaid
"""

# save mermaid diagram
with open(output_dir / "architecture.md", "w", encoding="utf-8") as f:
    f.write(mermaid_diagram)

# export agent metadata
agents_meta = {
    "orchestrator": {
        "emoji": "🧑‍✈️",
        "name": "Orchestrator",
        "role": "System brain",
        "input": "User natural language query",
        "output": "Structured intent + session context",
        "uses_llm": True
    },
    "memory": {
        "emoji": "🧬",
        "name": "Memory Agent",
        "role": "Persistent state manager",
        "input": "User ID",
        "output": "Long-term taste profile",
        "uses_llm": False
    },
    "taste_recommender": {
        "emoji": "🎯",
        "name": "Taste DJ",
        "role": "Familiar recommendations",
        "input": "User preferences + library",
        "output": "Ranked familiar tracks (~70%)",
        "uses_llm": False
    },
    "explorer": {
        "emoji": "🧪",
        "name": "Chaos DJ",
        "role": "Novel discoveries",
        "input": "User profile + library",
        "output": "High-novelty tracks (~30%)",
        "uses_llm": False
    },
    "safety": {
        "emoji": "🛡️",
        "name": "Safety Agent",
        "role": "Content policy enforcement",
        "input": "Candidate tracks + rules",
        "output": "Filtered tracks + logs",
        "uses_llm": False
    },
    "critic": {
        "emoji": "🧑‍⚖️",
        "name": "Critic",
        "role": "Multi-objective curator",
        "input": "All candidates + context",
        "output": "Final ranked playlist",
        "uses_llm": False
    },
    "explainer": {
        "emoji": "🌈",
        "name": "Storyteller",
        "role": "Human-friendly explanations",
        "input": "Playlist + agent logs",
        "output": "Engaging summary",
        "uses_llm": True
    },
    "feedback": {
        "emoji": "📊",
        "name": "Feedback Agent",
        "role": "Learning & adaptation",
        "input": "User actions (like/dislike)",
        "output": "Updated user profile",
        "uses_llm": False
    }
}

with open(output_dir / "agents_metadata.json", "w") as f:
    json.dump(agents_meta, f, indent=2)

# export workflow structure
workflow_structure = {
    "nodes": [
        "initialize",
        "orchestrator",
        "memory",
        "recommenders (parallel: taste + explorer)",
        "safety",
        "critic",
        "explainer",
        "done"
    ],
    "edges": [
        {"from": "initialize", "to": "orchestrator"},
        {"from": "orchestrator", "to": "memory", "condition": "no error"},
        {"from": "memory", "to": "recommenders"},
        {"from": "recommenders", "to": "safety"},
        {"from": "safety", "to": "critic", "condition": "no human review needed"},
        {"from": "safety", "to": "human_review", "condition": "review required"},
        {"from": "human_review", "to": "critic"},
        {"from": "critic", "to": "explainer"},
        {"from": "explainer", "to": "done"},
        {"from": "done", "to": "END"}
    ],
    "parallel_branches": [
        ["taste_recommender", "explorer"]
    ],
    "conditional_routing": [
        {"node": "orchestrator", "conditions": ["error_check"]},
        {"node": "safety", "conditions": ["human_review_check"]}
    ]
}

with open(output_dir / "workflow_structure.json", "w") as f:
    json.dump(workflow_structure, f, indent=2)
