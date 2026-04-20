import concurrent.futures
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup

from backend.agents.models import RawArticle, RawHeadline

# Daftar User-Agent modern untuk menghindari blokir IP (Anti-Bot)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

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
        user_agent: str | None = None,
    ) -> None:
        self.sources_file = sources_file
        self.processed_urls_file = processed_urls_file
        self.timeout_seconds = timeout_seconds

    def _get_random_headers(self, referer: str | None = None) -> dict:
        """Menghasilkan header acak untuk meniru browser sungguhan."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        if referer:
            headers["Referer"] = referer
        return headers

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

    def fetch_new_headlines(self, max_total: int = 150) -> tuple[list[RawHeadline], set[str]]:
        sources = self.load_sources()
        already_processed = self.load_processed_urls()
        per_source_limit = max(5, max_total // len(sources)) if sources else 10

        print(f"[PROCESS] Memindai {len(sources)} sumber (Jatah: {per_source_limit} per sumber)...")
        headlines: list[RawHeadline] = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(self._load_rss_entries_standalone, s.url): s for s in sources
            }
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    entries = future.result()
                    count = 0
                    for entry in entries:
                        if count >= per_source_limit:
                            break
                        url = (entry.get("link") or "").strip()
                        if url and url not in already_processed:
                            headlines.append(
                                RawHeadline(
                                    url=url,
                                    title=(entry.get("title") or "(tanpa judul)").strip(),
                                    source=source.name,
                                    published_at=self._parse_published_datetime(entry),
                                    category_hint=source.category_hint,
                                )
                            )
                            count += 1
                except Exception:
                    continue

        return headlines, already_processed

    def fetch_full_contents(self, headlines: list[RawHeadline]) -> list[RawArticle]:
        if not headlines:
            return []

        print(f"[PROCESS] Mengambil konten lengkap untuk {len(headlines)} berita terpilih...")
        articles: list[RawArticle] = []
        
        # Jitter: Tambahkan delay acak kecil antar request untuk meniru manusia
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_headline = {
                executor.submit(self._fetch_article_content_standalone, h.url): h
                for h in headlines
            }
            for future in concurrent.futures.as_completed(future_to_headline):
                headline = future_to_headline[future]
                try:
                    content = future.result()
                    if content:
                        articles.append(
                            RawArticle(
                                url=headline.url,
                                title=headline.title,
                                content=content,
                                source=headline.source,
                                published_at=headline.published_at,
                                category_hint=headline.category_hint,
                                cluster_id=getattr(headline, "cluster_id", -1),
                            )
                        )
                except Exception:
                    continue
        return articles

    def scrape_new_articles(self, max_per_source: int = 15) -> tuple[list[RawArticle], set[str]]:
        headlines, already_processed = self.fetch_new_headlines(max_per_source=max_per_source)
        if not headlines:
            return [], already_processed

        random.shuffle(headlines)
        selected = headlines[:50]
        
        articles = self.fetch_full_contents(selected)
        newly_processed = set(already_processed)
        for a in articles:
            newly_processed.add(a.url)
            
        return articles, newly_processed

    def _load_rss_entries_standalone(self, feed_url: str) -> list[dict]:
        try:
            # Jitter: Jangan request secara brutal, beri nafas sedikit
            time.sleep(random.uniform(0.5, 1.5))
            headers = self._get_random_headers()
            with httpx.Client(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
                response = client.get(feed_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
                return list(parsed.entries)
        except Exception:
            return []

    def _fetch_article_content_standalone(self, url: str) -> str:
        try:
            # Jitter: Penting saat mengambil Full Content (halaman web asli)
            time.sleep(random.uniform(1.0, 3.0))
            
            # Pasang Referer acak (berpura-pura datang dari Google atau Home)
            domain = "/".join(url.split("/")[:3])
            headers = self._get_random_headers(referer=domain)
            
            with httpx.Client(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                
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
