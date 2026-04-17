from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RawArticle:
    url: str
    title: str
    content: str
    source: str
    published_at: datetime
    category_hint: str


@dataclass(slots=True)
class FilteredArticle:
    url: str
    title: str
    content: str
    source: str
    published_at: datetime
    category: str
    category_hint: str


def prepare_document(article: RawArticle | FilteredArticle, max_chars: int = 2000) -> str:
    content = article.content[:max_chars]
    date_str = article.published_at.strftime("%d %B %Y")
    category = getattr(article, "category", article.category_hint)
    return (
        f"Judul: {article.title}\n"
        f"Kategori: {category}\n"
        f"Sumber: {article.source}\n"
        f"Tanggal: {date_str}\n\n"
        f"{content}"
    )
