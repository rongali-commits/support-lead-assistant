from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {"a", "an", "and", "are", "can", "do", "for", "i", "is", "of", "the", "to", "you"}


@dataclass(frozen=True)
class Article:
    article_id: str
    title: str
    content: str


@dataclass(frozen=True)
class SearchResult:
    article: Article
    score: int


class KnowledgeBase:
    def __init__(self, articles: list[Article]) -> None:
        self.articles = articles

    @classmethod
    def from_json(cls, path: Path) -> "KnowledgeBase":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls([Article(**item) for item in payload])

    def search(self, question: str, limit: int = 2) -> list[SearchResult]:
        query_tokens = _tokens(question)
        ranked: list[SearchResult] = []
        for article in self.articles:
            title_tokens = _tokens(article.title)
            body_tokens = _tokens(article.content)
            score = len(query_tokens & body_tokens) + 2 * len(query_tokens & title_tokens)
            if score:
                ranked.append(SearchResult(article=article, score=score))
        return sorted(ranked, key=lambda item: (-item.score, item.article.title))[:limit]


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if token not in STOP_WORDS}

