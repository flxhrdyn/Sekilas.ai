from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import httpx


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        dashboard_url: str = "",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.bot_token = bot_token.strip()
        self.chat_id = chat_id.strip()
        self.dashboard_url = dashboard_url.strip()
        self.timeout_seconds = timeout_seconds

    def send_digest(self, digest_record: Mapping[str, Any]) -> None:
        message = self._format_digest_message(digest_record)
        self._send_text(message)

    def _send_text(self, text: str) -> None:
        if not self.bot_token or not self.chat_id:
            raise RuntimeError("Telegram bot token/chat id belum dikonfigurasi.")

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text[:3900],
            "disable_web_page_preview": True,
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok", False):
                raise RuntimeError(f"Gagal kirim Telegram: {data}")

    def _format_digest_message(self, digest_record: Mapping[str, Any]) -> str:
        date_str = str(digest_record.get("date", datetime.utcnow().strftime("%Y-%m-%d")))
        headline = str(digest_record.get("headline", "Belum ada headline."))
        category_digests = digest_record.get("category_digests", {})
        if not isinstance(category_digests, dict):
            category_digests = {}

        lines: list[str] = [
            "Sekilas.ai Daily Digest",
            f"Date: {date_str}",
            "",
            "Headline:",
            headline,
            "",
            "Per Kategori:",
        ]

        if not category_digests:
            lines.append("- Tidak ada ringkasan kategori.")
        else:
            for category, items in category_digests.items():
                entries = items if isinstance(items, list) else []
                lines.append(f"- {category} ({len(entries)} artikel)")
                for item in entries[:3]:
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title", "Tanpa judul"))
                    source = str(item.get("source", "unknown"))
                    lines.append(f"  * {title} | {source}")

        if self.dashboard_url:
            lines.extend(["", f"Dashboard: {self.dashboard_url}"])

        return "\n".join(lines)
