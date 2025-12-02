from typing import List, Optional, Literal, TypedDict, Annotated, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import operator


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
    
    def __eq__(self, other):
        if not isinstance(other, Song):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


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
    explicit_filter: bool = False
    language_prefs: List[str] = Field(default_factory=list)
    novelty_tolerance: float = 0.3


class CandidateTrack(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=False)
    
    song: Any
    score: float
    source_agent: str
    reason: str
    novelty_score: float = 0.0
    confidence: float = 1.0


class SessionContext(BaseModel):
    activity: Optional[str] = None
    duration_minutes: Optional[int] = None
    mood: Optional[str] = None
    time_of_day: Optional[str] = None


class AgentLog(BaseModel):
    agent_name: str
    action: str
    details: str


class Playlist(BaseModel):
    title: str
    description: Optional[str] = None
    songs: List[Song] = Field(default_factory=list)


class AppState(TypedDict):
    user_id: str
    query: str
    intent: str
    preferences: UserPreferences
    session_context: SessionContext
    candidate_tracks: Annotated[List[CandidateTrack], operator.add]
    final_playlist: List[Song]
    explanations: Annotated[List[str], operator.add]
    logs: Annotated[List[AgentLog], operator.add]
    library: List[Song]
    error: Optional[str]
    requires_human_review: bool
    feedback: Optional[dict]


class Intent(BaseModel):
    action: Literal[
        "search", "recommend", "playlist_create", "playlist_expand", "analyze", "explain", "update_prefs"
    ]
    preferences: UserPreferences
