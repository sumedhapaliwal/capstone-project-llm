from __future__ import annotations
from typing import List
import numpy as np

from src.music_agent.state import Song, UserPreferences
from src.music_agent.tools.library import MusicLibrary


def score_song(s: Song, prefs: UserPreferences) -> float:
    score = 0.0
    if prefs.query:
        q = prefs.query.lower()
        if q in (s.name.lower() + " " + s.artist.lower()):
            score += 1.0
    for g in prefs.genres:
        if g in s.genres:
            score += 0.8
    for t in prefs.tags:
        if t in s.tags:
            score += 0.6
    for m in prefs.moods:
        if s.mood == m:
            score += 0.5
    if prefs.min_year and s.year and s.year >= prefs.min_year:
        score += 0.2
    if prefs.max_year and s.year and s.year <= prefs.max_year:
        score += 0.2
    if s.popularity:
        score += (s.popularity / 100.0) * 0.3
    return score


def recommend_by_prefs(lib: MusicLibrary, prefs: UserPreferences, k: int) -> List[Song]:
    candidates = lib.filter(
        genres=prefs.genres or None,
        artists=prefs.artists or None,
        tags=prefs.tags or None,
        moods=prefs.moods or None,
        min_year=prefs.min_year,
        max_year=prefs.max_year,
    )
    if not candidates:
        candidates = lib.songs

    scored = [(s, score_song(s, prefs)) for s in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in scored[:k]]
