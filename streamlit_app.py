import os
import json
import random
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from src.music_agent.state import UserPreferences, SessionContext
from src.music_agent.graph import invoke_workflow, build_multi_agent_graph
from src.music_agent.tools.library import load_default_library
from src.music_agent.agents.memory import update_user_memory
from src.music_agent.agents.refiner import refiner_agent, namer_agent

load_dotenv()

st.set_page_config(
    page_title="Music Intelligence",
    page_icon="♫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

playlists_file = Path("src/music_agent/data/saved_playlists.json")

def load_saved_playlists():
    if playlists_file.exists():
        with open(playlists_file, "r") as f:
            return json.load(f)
    return []

def save_playlist_to_file(playlist_data):
    playlists_file.parent.mkdir(parents=True, exist_ok=True)
    playlists = load_saved_playlists()
    playlists.append(playlist_data)
    with open(playlists_file, "w") as f:
        json.dump(playlists, f, indent=2)

if "saved_playlists" not in st.session_state:
    st.session_state.saved_playlists = load_saved_playlists()

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #2d1b4e 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    .song-card {
        background: rgba(30, 30, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        display: flex;
        gap: 1.2rem;
        align-items: center;
    }
    
    .album-cover {
        width: 80px;
        height: 80px;
        border-radius: 8px;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        flex-shrink: 0;
    }
    
    .song-info {
        flex: 1;
    }
    
    .song-card:hover {
        background: rgba(40, 40, 60, 0.9);
        border-color: rgba(255, 255, 255, 0.15);
        transform: translateY(-2px);
        cursor: pointer;
    }
    
    .song-card-clickable {
        cursor: pointer;
        user-select: none;
        position: relative;
    }
    
    button[kind="secondary"][aria-label*="toggle"] {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
        background: transparent !important;
        border: none !important;
    }
    
    .song-info .song-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 0.3rem;
    }
    
    .song-info .song-artist {
        font-size: 0.95rem;
        color: #a0a0a0;
        margin-bottom: 0.5rem;
    }
    
    .song-info .song-meta {
        font-size: 0.8rem;
        color: #707070;
    }
    
    .spotify-card {
        background: rgba(30, 30, 46, 0.8);
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
        min-width: 160px;
    }
    
    .spotify-card:hover {
        background: rgba(45, 45, 65, 0.9);
        transform: translateY(-4px);
    }
    
    .spotify-card .album-cover {
        width: 100%;
        aspect-ratio: 1;
        border-radius: 6px;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    
    .spotify-card .song-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .spotify-card .song-artist {
        font-size: 0.85rem;
        color: #a0a0a0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #e0e0e0;
        margin-bottom: 1rem;
        margin-top: 2rem;
    }
    
    .action-row {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.8rem;
        justify-content: center;
    }
    
    .icon-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 1px solid rgba(255, 255, 255, 0.15);
        background: rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 1.1rem;
    }
    
    .icon-btn:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: scale(1.1);
    }
    

    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #b0b0b0;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid rgba(75, 85, 120, 0.4) !important;
        background: rgba(15, 18, 30, 0.95) !important;
        color: #e8e8e8 !important;
        padding: 0.9rem 1.2rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: rgba(139, 92, 246, 0.7) !important;
        background: rgba(18, 22, 38, 1) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    }
    
    .stTextInput input::placeholder {
        color: rgba(160, 160, 180, 0.5) !important;
    }
    
    .stMultiSelect [data-baseweb="select"] {
        background: rgba(15, 18, 30, 0.95);
        border: 1px solid rgba(75, 85, 120, 0.4);
        border-radius: 10px;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background: rgba(255, 255, 255, 0.15);
        color: #e0e0e0;
        border: none;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 18, 30, 0.95);
        border: 1px solid rgba(75, 85, 120, 0.4);
        border-radius: 10px;
    }
    
    .stButton button {
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border: none;
        background: rgba(255, 255, 255, 0.12);
        color: #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.18);
        transform: translateY(-2px);
    }
    
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #7d8ef7 0%, #8a5cb8 100%);
    }
    
    .app-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
        color: white;
    }
    
    .app-title {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    
    .app-subtitle {
        font-size: 1rem;
        color: #b0b0b0;
        font-weight: 400;
    }
    
    h2, h3 {
        color: #e0e0e0 !important;
    }
    
    p, label {
        color: #b0b0b0 !important;
    }
    
    .stAlert {
        background: rgba(30, 30, 46, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Load library and user preferences
lib = load_default_library()
prefs_file = Path("src/music_agent/data/user_prefs.json")

def load_user_prefs():
    if prefs_file.exists():
        with open(prefs_file, "r") as f:
            return json.load(f)
    return {
        "liked_songs": [],
        "disliked_songs": [],
        "preferred_genres": [],
        "preferred_moods": [],
        "preferred_artists": []
    }

def save_user_prefs(prefs):
    with open(prefs_file, "w") as f:
        json.dump(prefs, f, indent=2)

if "user_prefs" not in st.session_state:
    st.session_state.user_prefs = load_user_prefs()

if "discovery_index" not in st.session_state:
    st.session_state.discovery_index = 0

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "active_refinement" not in st.session_state:
    st.session_state.active_refinement = False

st.markdown("""
<div class="app-header">
    <div class="app-title">Music Intelligence</div>
    <div class="app-subtitle">AI-Powered Playlist Creation</div>
</div>
""", unsafe_allow_html=True)

mistral_key = os.getenv("MISTRAL_API_KEY", "")
if not mistral_key or mistral_key == "your-mistral-api-key":
    st.warning("Configure MISTRAL_API_KEY in .env file to enable AI features")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Create Playlist", "Refine Playlist", "Discover", "Saved Playlists", "My Music"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        nl_query = st.text_input(
            "Describe your perfect playlist",
            placeholder="e.g., energetic workout songs from the 2010s"
        )
    
    with col2:
        size = st.select_slider("Songs", options=list(range(5, 31, 5)), value=10)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        genres = st.multiselect(
            "Filter by Genre",
            sorted({g for s in lib.songs for g in s.genres}),
            placeholder="Any Genre"
        )
    
    with col2:
        moods = st.multiselect(
            "Filter by Mood",
            sorted({s.mood for s in lib.songs if s.mood}),
            placeholder="Any Mood"
        )
    
    with col3:
        tags = st.multiselect(
            "Filter by Tags",
            sorted({t for s in lib.songs for t in s.tags}),
            placeholder="Any Tags"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Generate Playlist", use_container_width=True):
        if not mistral_key or mistral_key == "your-mistral-api-key":
            st.error("Configure MISTRAL_API_KEY to use AI features")
        else:
            with st.spinner("Multi-agent system generating playlist..."):
                try:
                    result = invoke_workflow(
                        query=nl_query or "recommend me some songs",
                        user_id="default_user"
                    )
                    
                    if result.get("error"):
                        st.error(f"Error: {result['error']}")
                    else:
                        st.session_state.last_result = result
                        st.session_state.active_refinement = True
                        
                        playlist_title, playlist_desc = namer_agent(result)
                        st.session_state.playlist_title = playlist_title
                        st.session_state.playlist_desc = playlist_desc
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    if st.session_state.get("last_result"):
        result = st.session_state.last_result
        
        with st.expander("Agent Activity Log", expanded=False):
            for log in result["logs"]:
                st.markdown(f"**{log.agent_name}**: {log.details}")
        
        if result["explanations"]:
            st.success(result["explanations"][0])
        
        playlist_title = st.session_state.get("playlist_title", "Your Playlist")
        playlist_desc = st.session_state.get("playlist_desc", "")
        
        st.markdown(f"### {playlist_title}")
        st.caption(playlist_desc)
        
        col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
        with col_save2:
            if st.button("Save This Playlist", use_container_width=True, key="save_current_playlist"):
                playlist_data = {
                    "title": playlist_title,
                    "description": playlist_desc,
                    "songs": [{
                        "id": s.id,
                        "name": s.name,
                        "artist": s.artist,
                        "album": s.album,
                        "year": s.year,
                        "genres": s.genres
                    } for s in result["final_playlist"]],
                    "created_at": pd.Timestamp.now().isoformat()
                }
                save_playlist_to_file(playlist_data)
                st.session_state.saved_playlists = load_saved_playlists()
                st.success("✓ Playlist saved! Check the 'Saved Playlists' tab.")
                st.balloons()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        for idx, song in enumerate(result["final_playlist"]):
            cover = song.cover_url if hasattr(song, 'cover_url') and song.cover_url else "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop"
            
            with st.container():
                st.markdown(f"""
                <div class="song-card song-card-clickable">
                    <img src="{cover}" class="album-cover" alt="{song.album}">
                    <div class="song-info">
                        <div class="song-title">{song.name}</div>
                        <div class="song-artist">{song.artist}</div>
                        <div class="song-meta">{song.album} • {song.year} • {', '.join(song.genres)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.session_state.get(f"show_modal_{song.id}", False):
                with st.container():
                    st.markdown("---")
                    col_d1, col_d2, col_d3 = st.columns([2, 2, 0.5])
                    with col_d1:
                        st.metric("Mood", song.mood or "N/A")
                        st.metric("Energy", f"{song.energy:.0%}" if song.energy else "N/A")
                        st.metric("Danceability", f"{song.danceability:.0%}" if song.danceability else "N/A")
                    with col_d2:
                        st.metric("Valence", f"{song.valence:.0%}" if song.valence else "N/A")
                        st.metric("Popularity", song.popularity or "N/A")
                        st.write("**Tags:**", ", ".join(song.tags) if song.tags else "N/A")
                    with col_d3:
                        if st.button("▲", key=f"collapse_{song.id}"):
                            st.session_state[f"show_modal_{song.id}"] = False
                            st.rerun()
                    st.markdown("---")
            else:
                if st.button("▼", key=f"expand_{song.id}"):
                    st.session_state[f"show_modal_{song.id}"] = True
                    st.rerun()

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not st.session_state.get("last_result") and len(st.session_state.saved_playlists) > 0:
        st.subheader("Load a Saved Playlist to Refine")
        st.caption("Select a playlist from your saved collection")
        
        saved_playlists = st.session_state.saved_playlists
        
        for idx, pl_data in enumerate(reversed(saved_playlists)):
            with st.expander(f"{pl_data['title']} - {len(pl_data['songs'])} songs", expanded=False):
                st.caption(f"Created: {pd.Timestamp(pl_data['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
                if pl_data.get("description"):
                    st.write(pl_data["description"])
                
                if st.button("Load This Playlist for Refinement", key=f"load_for_refine_{idx}"):
                    from src.music_agent.state import Song
                    
                    loaded_songs = []
                    for song_data in pl_data["songs"]:
                        full_song = next((s for s in lib.songs if s.id == song_data['id']), None)
                        if full_song:
                            loaded_songs.append(full_song)
                    
                    mock_result = {
                        "query": "Loaded from saved playlist",
                        "final_playlist": loaded_songs,
                        "preferences": UserPreferences(
                            genres=[],
                            size=len(loaded_songs),
                            novelty_tolerance=0.5
                        ),
                        "session_context": SessionContext(
                            activity=None,
                            mood=None,
                            duration=None
                        ),
                        "logs": [],
                        "explanations": [pl_data.get("description", "")]
                    }
                    
                    st.session_state.last_result = mock_result
                    st.session_state.playlist_title = pl_data["title"]
                    st.session_state.playlist_desc = pl_data.get("description", "")
                    st.session_state.active_refinement = True
                    st.session_state.conversation_history = []
                    st.session_state.original_playlist = loaded_songs.copy()
                    st.session_state.new_songs = set()
                    st.rerun()
    
    if not st.session_state.get("last_result"):
        st.info("Create a playlist first, or load a saved one above to refine it!")
    else:
        result = st.session_state.last_result
        
        col_actions1, col_actions2 = st.columns([1, 1])
        
        with col_actions1:
            if st.button("💾 Save Refined Playlist", use_container_width=True, type="primary"):
                playlist_title = st.session_state.get("playlist_title", "Refined Playlist")
                playlist_desc = st.session_state.get("playlist_desc", "")
                
                playlist_data = {
                    "title": playlist_title,
                    "description": playlist_desc,
                    "songs": [{
                        "id": s.id,
                        "name": s.name,
                        "artist": s.artist,
                        "album": s.album,
                        "year": s.year,
                        "genres": s.genres
                    } for s in result["final_playlist"]],
                    "created_at": pd.Timestamp.now().isoformat()
                }
                save_playlist_to_file(playlist_data)
                st.session_state.saved_playlists = load_saved_playlists()
                
                st.session_state.last_result = None
                st.session_state.conversation_history = []
                st.session_state.active_refinement = False
                st.session_state.playlist_title = None
                st.session_state.playlist_desc = None
                
                st.success("✓ Playlist saved!")
                st.balloons()
                st.rerun()
        
        with col_actions2:
            if st.button("← Back to Playlist Selection", use_container_width=True):
                st.session_state.last_result = None
                st.session_state.conversation_history = []
                st.session_state.active_refinement = False
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_chat, col_playlist = st.columns([1, 1])
        
        with col_chat:
            st.subheader("Conversational Refinement")
            st.caption("Chat with the system to adjust your playlist")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            current_size = len(result["final_playlist"])
            if "original_playlist" not in st.session_state:
                st.session_state.original_playlist = result["final_playlist"].copy()
            
            if "target_size" not in st.session_state:
                st.session_state.target_size = current_size
            
            new_size = st.slider(
                "Playlist Size",
                min_value=5,
                max_value=30,
                value=st.session_state.target_size,
                key="playlist_size_slider",
                help="Adjust the number of songs in your playlist"
            )
            
            if new_size != st.session_state.target_size:
                st.session_state.target_size = new_size
            
            if st.button("Apply Size Change", disabled=(new_size == current_size)):
                with st.spinner("Adjusting playlist size..."):
                    if new_size > current_size:
                        songs_needed = new_size - current_size
                        
                        temp_result = invoke_workflow(
                            query=result["query"],
                            user_id="default_user",
                            preferences={
                                "genres": result["preferences"].genres,
                                "size": songs_needed + 5,
                                "novelty_tolerance": result["preferences"].novelty_tolerance
                            }
                        )
                        
                        current_ids = {s.id for s in result["final_playlist"]}
                        new_candidates = [s for s in temp_result["final_playlist"] if s.id not in current_ids][:songs_needed]
                        
                        combined_playlist = result["final_playlist"] + new_candidates
                        
                        result["final_playlist"] = combined_playlist
                        st.session_state.last_result = result
                        st.session_state.new_songs = {s.id for s in new_candidates}
                        st.session_state.target_size = new_size
                        
                        new_title, new_desc = namer_agent(result)
                        st.session_state.playlist_title = new_title
                        st.session_state.playlist_desc = new_desc
                    else:
                        result["final_playlist"] = result["final_playlist"][:new_size]
                        st.session_state.last_result = result
                        st.session_state.new_songs = set()
                        st.session_state.target_size = new_size
                        
                        new_title, new_desc = namer_agent(result)
                        st.session_state.playlist_title = new_title
                        st.session_state.playlist_desc = new_desc
                    
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.session_state.conversation_history:
                for msg in st.session_state.conversation_history:
                    if msg["role"] == "user":
                        st.chat_message("user").write(msg["content"])
                    else:
                        st.chat_message("assistant").write(msg["content"])
        
            user_input = st.chat_input("Tell me how to adjust the playlist...")
            
            if user_input:
                st.session_state.conversation_history.append({"role": "user", "content": user_input})
                
                with st.spinner("Analyzing your request..."):
                    state, modifications, analysis = refiner_agent(result, user_input)
                    
                    if modifications:
                        prefs_dict = {
                            "genres": result["preferences"].genres,
                            "size": result["preferences"].size,
                            "novelty_tolerance": result["preferences"].novelty_tolerance
                        }
                        
                        if "energy_adjustment" in modifications:
                            if result["preferences"].energy_range:
                                new_min = max(0, result["preferences"].energy_range[0] + modifications["energy_adjustment"])
                                new_max = min(1, result["preferences"].energy_range[1] + modifications["energy_adjustment"])
                                prefs_dict["energy_range"] = (new_min, new_max)
                            else:
                                base = 0.5 + modifications["energy_adjustment"]
                                prefs_dict["energy_range"] = (max(0, base - 0.2), min(1, base + 0.2))
                        
                        if "novelty_adjustment" in modifications:
                            prefs_dict["novelty_tolerance"] = max(0, min(1, prefs_dict["novelty_tolerance"] + modifications["novelty_adjustment"]))
                        
                        refined_result = invoke_workflow(
                            query=result["query"],
                            user_id="default_user",
                            preferences=prefs_dict
                        )
                        
                        original_ids = {s.id for s in st.session_state.original_playlist}
                        new_songs = {s.id for s in refined_result["final_playlist"] if s.id not in original_ids}
                        
                        st.session_state.last_result = refined_result
                        st.session_state.new_songs = new_songs
                        
                        new_title, new_desc = namer_agent(refined_result)
                        st.session_state.playlist_title = new_title
                        st.session_state.playlist_desc = new_desc
                        
                        response = f"✓ Adjusted! {analysis[:150]}"
                        st.session_state.conversation_history.append({"role": "assistant", "content": response})
                        
                        st.rerun()
                    else:
                        response = "I understood your request but couldn't determine specific changes. Try: 'more energetic', 'calmer', 'more variety', 'more familiar'"
                        st.session_state.conversation_history.append({"role": "assistant", "content": response})
                        st.rerun()
        
        with col_playlist:
            st.subheader("Current Playlist")
            
            if st.session_state.get("playlist_title"):
                st.markdown(f"**{st.session_state.playlist_title}**")
                st.caption(st.session_state.playlist_desc)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if "new_songs" not in st.session_state:
                st.session_state.new_songs = set()
            
            for idx, song in enumerate(result["final_playlist"]):
                is_new = song.id in st.session_state.new_songs
                cover = song.cover_url if hasattr(song, 'cover_url') and song.cover_url else "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop"
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 6px; border-left: {'3px solid #8b5cf6' if is_new else '3px solid transparent'};">
                    <img src="{cover}" style="width: 45px; height: 45px; border-radius: 4px; object-fit: cover; margin-right: 12px;" alt="{song.album}">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 13px; font-weight: 500; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {song.name} {'✨' if is_new else ''}
                        </div>
                        <div style="font-size: 11px; color: rgba(255,255,255,0.6); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {song.artist}
                        </div>
                    </div>
                    <div style="font-size: 10px; color: rgba(255,255,255,0.4); margin-left: 8px; white-space: nowrap;">
                        {', '.join(song.genres[:1])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    
    saved_playlists = st.session_state.saved_playlists
    
    st.subheader(f"Your Saved Playlists ({len(saved_playlists)})")
    
    if not saved_playlists:
        st.info("No saved playlists yet. Create a playlist and save it to see it here!")
    else:
        for idx, pl_data in enumerate(reversed(saved_playlists)):
            with st.expander(f"{pl_data['title']} - {len(pl_data['songs'])} songs", expanded=False):
                if pl_data.get("description"):
                    st.write(pl_data["description"])
                
                st.caption(f"Created: {pd.Timestamp(pl_data['created_at']).strftime('%B %d, %Y at %I:%M %p')}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                for song_data in pl_data["songs"]:
                    full_song = next((s for s in lib.songs if s.id == song_data['id']), None)
                    cover = full_song.cover_url if full_song and hasattr(full_song, 'cover_url') and full_song.cover_url else "https://via.placeholder.com/80x80/1a1a2e/8b5cf6?text=No+Cover"
                    st.markdown(f"""
                    <div class="song-card">
                        <img src="{cover}" class="album-cover" alt="{song_data['album']}">
                        <div class="song-info">
                            <div class="song-title">{song_data['name']}</div>
                            <div class="song-artist">{song_data['artist']}</div>
                            <div class="song-meta">{song_data['album']} • {song_data['year']} • {', '.join(song_data['genres'])}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button(f"Delete Playlist", key=f"saved_delete_playlist_{idx}"):
                    saved_playlists.pop(len(saved_playlists) - 1 - idx)
                    with open(playlists_file, "w") as f:
                        json.dump(saved_playlists, f, indent=2)
                    st.session_state.saved_playlists = saved_playlists
                    st.rerun()

with tab5:
    st.markdown("<br>", unsafe_allow_html=True)
    
    user_prefs = st.session_state.user_prefs
    liked_songs = [s for s in lib.songs if s.id in user_prefs["liked_songs"]]
    
    st.subheader(f"Liked Songs ({len(liked_songs)})")
    
    if not liked_songs:
        st.info("No liked songs yet. Visit the Discover tab to find music you love!")
    else:
        for idx, song in enumerate(liked_songs):
            cover = song.cover_url if hasattr(song, 'cover_url') and song.cover_url else "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop"
            
            with st.container():
                st.markdown(f"""
                <div class="song-card song-card-clickable">
                    <img src="{cover}" class="album-cover" alt="{song.album}">
                    <div class="song-info">
                        <div class="song-title">{song.name}</div>
                        <div class="song-artist">{song.artist}</div>
                        <div class="song-meta">
                            {song.album} • {song.year} • {', '.join(song.genres)}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.session_state.get(f"show_mymusic_modal_{song.id}", False):
                with st.container():
                    st.markdown("---")
                    col_d1, col_d2, col_d3 = st.columns([2, 2, 0.5])
                    with col_d1:
                        st.metric("Mood", song.mood or "N/A")
                        st.metric("Energy", f"{song.energy:.0%}" if song.energy else "N/A")
                        st.metric("Danceability", f"{song.danceability:.0%}" if song.danceability else "N/A")
                    with col_d2:
                        st.metric("Valence", f"{song.valence:.0%}" if song.valence else "N/A")
                        st.metric("Popularity", song.popularity or "N/A")
                        st.write("**Tags:**", ", ".join(song.tags) if song.tags else "N/A")
                    with col_d3:
                        if st.button("▲", key=f"mymusic_collapse_{song.id}"):
                            st.session_state[f"show_mymusic_modal_{song.id}"] = False
                            st.rerun()
                    st.markdown("---")
            else:
                if st.button("▼", key=f"mymusic_expand_{song.id}"):
                    st.session_state[f"show_mymusic_modal_{song.id}"] = True
                    st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if user_prefs["preferred_genres"] or user_prefs["preferred_moods"]:
        st.subheader("Your Preferences")
        
        if user_prefs["preferred_genres"]:
            st.write("**Favorite Genres:**", ", ".join(user_prefs["preferred_genres"][:5]))
        
        if user_prefs["preferred_moods"]:
            st.write("**Favorite Moods:**", ", ".join(user_prefs["preferred_moods"][:5]))
        
        if user_prefs["preferred_artists"]:
            st.write("**Favorite Artists:**", ", ".join(user_prefs["preferred_artists"][:5]))

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "discovery_mode" not in st.session_state:
        st.session_state.discovery_mode = "for_you"
    
    col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
    with col_t2:
        col_for, col_all = st.columns(2)
        with col_for:
            if st.button("For You", key="for_you_toggle", use_container_width=True,
                        type="primary" if st.session_state.discovery_mode == "for_you" else "secondary"):
                st.session_state.discovery_mode = "for_you"
                st.rerun()
        with col_all:
            if st.button("All Songs", key="all_songs_toggle", use_container_width=True,
                        type="primary" if st.session_state.discovery_mode == "all_songs" else "secondary"):
                st.session_state.discovery_mode = "all_songs"
                st.rerun()
    
    user_prefs = st.session_state.user_prefs
    excluded = set(user_prefs["liked_songs"] + user_prefs["disliked_songs"])
    
    if st.session_state.discovery_mode == "for_you":
        if user_prefs["preferred_genres"] or user_prefs["preferred_moods"]:
            available = [
                s for s in lib.songs 
                if s.id not in excluded and (
                    any(g in user_prefs["preferred_genres"] for g in s.genres) or
                    s.mood in user_prefs["preferred_moods"]
                )
            ]
        else:
            available = [s for s in lib.songs if s.id not in excluded]
    else:
        available = [s for s in lib.songs if s.id not in excluded]
    
    if not available:
        st.info("You've rated all available songs!")
    else:
        if st.session_state.discovery_index >= len(available):
            random.shuffle(available)
            st.session_state.discovery_index = 0
        
        song = available[st.session_state.discovery_index]
        cover = song.cover_url if hasattr(song, 'cover_url') and song.cover_url else "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop"
        
        st.markdown(f"""
        <div class="song-card">
            <img src="{cover}" class="album-cover" alt="{song.album}">
            <div class="song-info">
                <div class="song-title">{song.name}</div>
                <div class="song-artist">{song.artist}</div>
                <div class="song-meta">{song.album} • {song.year} • {', '.join(song.genres)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Dislike", key="dislike_main", use_container_width=True):
                user_prefs["disliked_songs"].append(song.id)
                save_user_prefs(user_prefs)
                st.session_state.discovery_index += 1
                st.rerun()
        
        with col2:
            if st.button("Skip", key="skip_main", use_container_width=True):
                st.session_state.discovery_index += 1
                st.rerun()
        
        with col3:
            if st.button("Like", key="like_main", use_container_width=True):
                user_prefs["liked_songs"].append(song.id)
                update_user_memory("default_user", {"liked_song": song.model_dump()})
                st.session_state.user_prefs = load_user_prefs()
                st.session_state.discovery_index += 1
                st.rerun()
