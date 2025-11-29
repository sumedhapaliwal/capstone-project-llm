from typing import List, Optional, Literal, TypedDict
from pydantic import BaseModel, Field


class Song(BaseModel):
    id: str
    name: str
    artist: str
    album: Optional[str] = None
    year: Optional[int] = None
    duration_sec: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[float] = None
    danceability: Optional[float] = None
    valence: Optional[float] = None
    popularity: Optional[int] = None
    cover_url: Optional[str] = None


class UserPreferences(BaseModel):
    query: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    artists: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    moods: List[str] = Field(default_factory=list)
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    energy_range: Optional[tuple[float, float]] = None
    danceability_range: Optional[tuple[float, float]] = None
    size: int = 10


class Playlist(BaseModel):
    title: str
    description: Optional[str] = None
    songs: List[Song] = Field(default_factory=list)


class AgentState(TypedDict):
    preferences: UserPreferences
    library: List[Song]
    candidate_songs: List[Song]
    playlist: Optional[Playlist]
    last_action: Optional[str]
    error: Optional[str]


class Intent(BaseModel):
    action: Literal[
        "search", "recommend", "playlist_create", "playlist_expand", "analyze"
    ]
    preferences: UserPreferences
