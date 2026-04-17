from __future__ import annotations

import concurrent.futures
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup

from backend.agents.models import RawArticle


@dataclass(slots=True)
class SourceConfig:
    name: str
    url: str
    category_hint: str


class NewsScraper:
    def __init__(
        self,
        sources_file: Path,
        processed_urls_file: Path,
        timeout_seconds: float = 20.0,
        user_agent: str = "sekilas-ai-agentic-rag/0.1",
    ) -> None:
        self.sources_file = sources_file
        self.processed_urls_file = processed_urls_file
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}

    def load_sources(self) -> list[SourceConfig]:
        with self.sources_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        sources = data.get("sources", [])
        out: list[SourceConfig] = []
        for item in sources:
            if not item.get("name") or not item.get("url"):
                continue
            out.append(
                SourceConfig(
                    name=item["name"],
                    url=item["url"],
                    category_hint=item.get("category_hint", "umum"),
                )
            )
        return out

    def load_processed_urls(self) -> set[str]:
        if not self.processed_urls_file.exists():
            return set()
        with self.processed_urls_file.open("r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}

    def save_processed_urls(self, processed_urls: Iterable[str]) -> None:
        urls = sorted(set(processed_urls))
        self.processed_urls_file.parent.mkdir(parents=True, exist_ok=True)
        with self.processed_urls_file.open("w", encoding="utf-8") as f:
            for url in urls:
                f.write(f"{url}\n")

    def scrape_new_articles(self, max_per_source: int = 15) -> tuple[list[RawArticle], set[str]]:
        sources = self.load_sources()
        already_processed = self.load_processed_urls()
        
        # 1. Fetch RSS feeds in parallel
        print(f"[PROCESS] Membaca {len(sources)} RSS feed secara paralel...")
        entries_with_sources: list[tuple[dict, SourceConfig]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_source = {
                executor.submit(self._load_rss_entries_standalone, s.url): s for s in sources
            }
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    entries = future.result()
                    # Hanya ambil entry yang belum pernah diproses
                    for entry in entries[:max_per_source]:
                        url = (entry.get("link") or "").strip()
                        if url and url not in already_processed:
                            entries_with_sources.append((entry, source))
                except Exception:
                    continue

        if not entries_with_sources:
            return [], already_processed

        # 2. Acak dan Batasi sebelum download konten (Optimasi Waktu)
        random.shuffle(entries_with_sources)
        entries_with_sources = entries_with_sources[:50]

        # 3. Fetch Article Contents in parallel
        print(f"[PROCESS] Mengambil konten {len(entries_with_sources)} artikel terpilih secara paralel...")
        articles: list[RawArticle] = []
        newly_processed = set(already_processed)

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_entry = {
                executor.submit(self._fetch_article_content_standalone, e["link"]): (e, s)
                for e, s in entries_with_sources
            }
            for future in concurrent.futures.as_completed(future_to_entry):
                entry, source = future_to_entry[future]
                try:
                    content = future.result()
                    if content:
                        url = (entry.get("link") or "").strip()
                        published_at = self._parse_published_datetime(entry)
                        title = (entry.get("title") or "(tanpa judul)").strip()

                        articles.append(
                            RawArticle(
                                url=url,
                                title=title,
                                content=content,
                                source=source.name,
                                published_at=published_at,
                                category_hint=source.category_hint,
                            )
                        )
                        newly_processed.add(url)
                except Exception:
                    continue

        return articles, newly_processed

    def _load_rss_entries_standalone(self, feed_url: str) -> list[dict]:
        try:
            with httpx.Client(timeout=self.timeout_seconds, headers=self.headers, follow_redirects=True) as client:
                response = client.get(feed_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
                return list(parsed.entries)
        except Exception:
            return []

    def _fetch_article_content_standalone(self, url: str) -> str:
        try:
            with httpx.Client(timeout=self.timeout_seconds, headers=self.headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                # Menggunakan lxml parser untuk kecepatan maksimal
                soup = BeautifulSoup(response.text, "lxml")
                for tag in soup(["script", "style", "noscript"]):
                    tag.extract()

                paragraphs = [
                    p.get_text(" ", strip=True)
                    for p in soup.find_all("p")
                    if p.get_text(" ", strip=True)
                ]
                text = "\n".join(paragraphs).strip()
                return text[:8000]
        except Exception:
            return ""

    def _parse_published_datetime(self, entry: dict) -> datetime:
        for key in ("published", "updated"):
            value = entry.get(key)
            if value:
                try:
                    dt = parsedate_to_datetime(value)
                    if dt.tzinfo is None:
                        return dt.replace(tzinfo=UTC)
                    return dt.astimezone(UTC)
                except Exception:
                    continue
        return datetime.now(UTC)
