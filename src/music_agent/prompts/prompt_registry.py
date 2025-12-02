from src.music_agent.prompts.prompt_manager import get_prompt_manager

pm = get_prompt_manager()

pm.register_prompt(
    agent_name="orchestrator",
    version="v1_concise",
    template="""Parse this music query into structured intent:
Query: {query}

Extract:
- Intent: (recommend/search/playlist_create)
- Genres: List any mentioned
- Mood: Overall emotional tone
- Activity: Context (workout/study/party/etc)
- Energy: (low/medium/high)

Respond in JSON format.""",
    variables=["query"],
    metadata={"style": "concise", "tokens": "~150"},
    set_active=True
)

pm.register_prompt(
    agent_name="orchestrator",
    version="v2_detailed",
    template="""You are a music intent analyzer. Parse the user's natural language query into structured data.

User Query: "{query}"

Analyze and extract:
1. Primary Intent: What does the user want? (recommend, search, create playlist, expand playlist)
2. Genre Preferences: Any specific genres mentioned or implied
3. Mood/Emotion: What emotional state or vibe is requested
4. Activity Context: What activity is this for (if any)
5. Energy Level: Desired intensity (calm/moderate/energetic)
6. Special Requests: Any unique requirements (discover new artists, familiar songs only, etc)

Provide a detailed JSON response with all extracted information.""",
    variables=["query"],
    metadata={"style": "detailed", "tokens": "~300"}
)

pm.register_prompt(
    agent_name="orchestrator",
    version="v3_conversational",
    template="""Hey! Let's understand what you're looking for.

You said: "{query}"

I need to figure out:
- What you want to do (discover songs? build a playlist?)
- What genres you're into
- The vibe you're going for
- Any specific activity this is for

Give me the details in JSON so I can hook you up with the perfect music.""",
    variables=["query"],
    metadata={"style": "conversational", "tokens": "~200"}
)

pm.register_prompt(
    agent_name="explainer",
    version="v1_storytelling",
    template="""Create a compelling story about this playlist:

User Query: {query}
Songs: {songs}
User Preferences: {preferences}

Write a narrative that:
1. Connects songs to the user's original request
2. Explains the emotional journey through the playlist
3. Highlights 2-3 standout tracks and why they fit
4. Makes the user excited to listen

Keep it under 150 words.""",
    variables=["query", "songs", "preferences"],
    metadata={"style": "storytelling", "max_words": 150},
    set_active=True
)

pm.register_prompt(
    agent_name="explainer",
    version="v2_technical",
    template="""Generate a technical explanation for this playlist recommendation:

Query: {query}
Selected Songs: {songs}
User Profile: {preferences}

Explain:
- Why each song was selected (genre match, energy level, mood)
- How the playlist balances familiarity vs discovery
- Statistical breakdown (avg energy, genre distribution)
- Reasoning behind song ordering

Be precise and data-driven.""",
    variables=["query", "songs", "preferences"],
    metadata={"style": "technical"}
)

pm.register_prompt(
    agent_name="explainer",
    version="v3_casual",
    template="""Yo! Here's why this playlist is perfect for you:

You wanted: {query}
I picked: {songs}
Based on: {preferences}

Quick breakdown of why these songs slap and how they match your vibe. Keep it real and fun.""",
    variables=["query", "songs", "preferences"],
    metadata={"style": "casual"}
)

pm.register_prompt(
    agent_name="refiner",
    version="v1_analytical",
    template="""Analyze this playlist refinement request:

Original Query: {original_query}
Current Playlist: {current_songs}
User Feedback: {feedback}
User Preferences: {preferences}

Determine:
1. What aspects to change (energy, genre, mood, artists)
2. Which songs to remove (if any)
3. What characteristics to emphasize
4. Specific adjustments (numeric ranges for energy, valence, etc)

Return structured modifications in JSON.""",
    variables=["original_query", "current_songs", "feedback", "preferences"],
    metadata={"style": "analytical"},
    set_active=True
)

pm.register_prompt(
    agent_name="refiner",
    version="v2_conversational",
    template="""User wants to adjust their playlist. Let's figure out what they mean:

They originally asked for: "{original_query}"
Current playlist has: {current_songs}
Now they're saying: "{feedback}"

What do they actually want changed? Break it down:
- Remove songs? Which type?
- Add more of something? What specifically?
- Change the overall vibe? How?

Give me actionable changes.""",
    variables=["original_query", "current_songs", "feedback", "preferences"],
    metadata={"style": "conversational"}
)

pm.register_prompt(
    agent_name="namer",
    version="v1_creative",
    template="""Create an awesome playlist title and description:

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

Your turn!""",
    variables=["songs", "query", "mood"],
    metadata={"style": "creative"},
    set_active=True
)

pm.register_prompt(
    agent_name="namer",
    version="v2_minimal",
    template="""Name this playlist:

Songs: {songs}
Query: {query}

Title (3-5 words):
Description (1 sentence):

Keep it simple and clear.""",
    variables=["songs", "query", "mood"],
    metadata={"style": "minimal"}
)

pm.register_prompt(
    agent_name="namer",
    version="v3_poetic",
    template="""Craft a poetic playlist name:

For these songs: {songs}
Inspired by: {query}
Emotion: {mood}

Create a title that:
- Evokes imagery and emotion
- Uses metaphor or wordplay
- Feels like art

Then write a lyrical description that makes people want to press play.""",
    variables=["songs", "query", "mood"],
    metadata={"style": "poetic"}
)

