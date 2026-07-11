"""Cartesia provider: voice discovery + TTS preview generation.
Cartesia natively supports Hebrew ('he') on Sonic 3+, so we can pick voices
actually trained/tuned for Hebrew rather than cross-synthesizing."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Iterator

import requests

BASE_URL = "https://api.cartesia.ai"
API_VERSION = "2026-03-01"
DEFAULT_TTS_MODEL = "sonic-3.5"


@dataclass
class CartesiaVoice:
    id: str
    name: str
    description: str = ""
    language: str = ""
    country: str | None = None
    gender: str = ""  # feminine | masculine | gender_neutral
    is_pro: bool = False
    is_public: bool = True
    preview_file_url: str | None = None
    created_at: str = ""


class CartesiaClient:
    def __init__(self, api_key: str | None = None, request_delay: float = 0.25):
        self.api_key = api_key or os.environ.get("CARTESIA_API_KEY")
        if not self.api_key:
            raise RuntimeError("CARTESIA_API_KEY not set")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Cartesia-Version": API_VERSION,
        })
        self.request_delay = request_delay

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        if not r.ok:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
        time.sleep(self.request_delay)
        return r.json()

    def iter_voices(
        self,
        language: str | None = None,
        gender: str | None = None,
        limit: int = 100,
        max_pages: int = 20,
        expand_preview: bool = True,
    ) -> Iterator[CartesiaVoice]:
        starting_after: str | None = None
        for _ in range(max_pages):
            params: list = [("limit", str(limit))]
            if language:
                params.append(("language", language))
            if gender:
                params.append(("gender", gender))
            if expand_preview:
                params.append(("expand[]", "preview_file_url"))
            if starting_after:
                params.append(("starting_after", starting_after))
            data = self._get("/voices", params=params)
            for raw in data.get("data", []):
                yield CartesiaVoice(
                    id=raw.get("id"),
                    name=raw.get("name") or "",
                    description=(raw.get("description") or "").strip(),
                    language=raw.get("language") or "",
                    country=raw.get("country"),
                    gender=(raw.get("gender") or "").lower(),
                    is_pro=bool(raw.get("is_pro")),
                    is_public=bool(raw.get("is_public", True)),
                    preview_file_url=raw.get("preview_file_url"),
                    created_at=raw.get("created_at") or "",
                )
            if not data.get("has_more"):
                break
            starting_after = data.get("next_page")
            if not starting_after:
                break

    def tts(
        self,
        voice_id: str,
        transcript: str,
        language: str,
        model_id: str = DEFAULT_TTS_MODEL,
    ) -> bytes:
        """Generate speech. Returns raw MP3 bytes."""
        payload = {
            "model_id": model_id,
            "transcript": transcript,
            "voice": {"mode": "id", "id": voice_id},
            "language": language,
            "output_format": {
                "container": "mp3",
                "sample_rate": 44100,
                "bit_rate": 128000,
            },
        }
        r = self.session.post(
            f"{BASE_URL}/tts/bytes",
            json=payload,
            headers={"Accept": "audio/mpeg"},
            timeout=60,
        )
        if not r.ok:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
        time.sleep(self.request_delay)
        return r.content
