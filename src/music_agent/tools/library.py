from __future__ import annotations
from typing import List, Dict, Any
import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.music_agent.state import Song


class MusicLibrary:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.songs: List[Song] = []
        self._tfidf = None
        self._matrix = None
        self._corpus: List[str] = []

    def load(self) -> int:
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.songs = [Song(**d) for d in data]

        self._corpus = [self._song_text(s) for s in self.songs]
        self._tfidf = TfidfVectorizer(stop_words="english")
        self._matrix = self._tfidf.fit_transform(self._corpus)
        return len(self.songs)

    def _song_text(self, s: Song) -> str:
        parts = [
            s.name,
            s.artist,
            s.album or "",
            " ".join(s.genres),
            " ".join(s.tags),
            s.mood or "",
            s.category or "",
        ]
        return " ".join([p for p in parts if p])

    def as_dicts(self, xs: List[Song]) -> List[Dict[str, Any]]:
        return [x.model_dump() for x in xs]

    def search(self, query: str, k: int = 10) -> List[Song]:
        if not query:
            return []
        q_vec = self._tfidf.transform([query])
        sims = cosine_similarity(q_vec, self._matrix).flatten()
        top_idx = np.argsort(-sims)[:k]
        return [self.songs[i] for i in top_idx]

    def filter(self,
               *,
               genres: List[str] | None = None,
               artists: List[str] | None = None,
               tags: List[str] | None = None,
               moods: List[str] | None = None,
               min_year: int | None = None,
               max_year: int | None = None) -> List[Song]:
        def ok(s: Song) -> bool:
            if genres and not any(g in s.genres for g in genres):
                return False
            if artists and s.artist not in artists:
                return False
            if tags and not any(t in s.tags for t in tags):
                return False
            if moods and (s.mood not in moods):
                return False
            if min_year and (s.year or 0) < min_year:
                return False
            if max_year and (s.year or 9999) > max_year:
                return False
            return True

        return [s for s in self.songs if ok(s)]

    def similarity(self, seeds: List[Song], k: int = 10) -> List[Song]:
        if not seeds:
            return []
        seed_texts = [self._song_text(s) for s in seeds]
        seed_vec = self._tfidf.transform([" \n".join(seed_texts)])
        sims = cosine_similarity(seed_vec, self._matrix).flatten()
        seed_ids = {s.id for s in seeds}
        order = np.argsort(-sims)
        result = []
        for i in order:
            if self.songs[i].id in seed_ids:
                continue
            result.append(self.songs[i])
            if len(result) >= k:
                break
        return result


def load_default_library() -> MusicLibrary:
    data_path = Path(__file__).parents[1] / "data" / "songs.json"
    lib = MusicLibrary(data_path)
    lib.load()
    return lib
