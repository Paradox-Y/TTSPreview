"""ElevenLabs provider: shared-library discovery + TTS preview generation."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Iterator

import requests

BASE_URL = "https://api.elevenlabs.io"
DEFAULT_TTS_MODEL = "eleven_multilingual_v2"


@dataclass
class SharedVoice:
    voice_id: str
    public_owner_id: str
    name: str
    category: str
    gender: str
    accent: str = ""
    age: str = ""
    descriptive: str = ""
    use_case: str = ""
    language: str = ""
    locale: str = ""
    description: str = ""
    preview_url: str | None = None
    usage_1y: int = 0
    usage_7d: int = 0
    cloned_by_count: int = 0
    free_users_allowed: bool = False
    verified_languages: list[dict] = field(default_factory=list)


class ElevenLabsClient:
    def __init__(self, api_key: str | None = None, request_delay: float = 0.25):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")
        self.session = requests.Session()
        self.session.headers.update({"xi-api-key": self.api_key})
        self.request_delay = request_delay

    def _get(self, path: str, **params) -> dict:
        r = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        if not r.ok:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
        time.sleep(self.request_delay)
        return r.json()

    def iter_shared_voices(
        self,
        category: str = "professional",
        language: str | None = None,
        gender: str | None = None,
        page_size: int = 100,
        max_pages: int = 20,
    ) -> Iterator[SharedVoice]:
        """Paginate through /v1/shared-voices (the public Voice Library)."""
        base_params: dict = {"category": category, "page_size": page_size}
        if language:
            base_params["language"] = language
        if gender:
            base_params["gender"] = gender
        for page in range(max_pages):
            params = {**base_params, "page": page}
            data = self._get("/v1/shared-voices", **params)
            voices = data.get("voices", [])
            for raw in voices:
                yield SharedVoice(
                    voice_id=raw.get("voice_id"),
                    public_owner_id=raw.get("public_owner_id"),
                    name=raw.get("name") or "",
                    category=raw.get("category") or "",
                    gender=(raw.get("gender") or "").lower(),
                    accent=raw.get("accent") or "",
                    age=raw.get("age") or "",
                    descriptive=raw.get("descriptive") or "",
                    use_case=raw.get("use_case") or "",
                    language=raw.get("language") or "",
                    locale=raw.get("locale") or "",
                    description=(raw.get("description") or "").strip(),
                    preview_url=raw.get("preview_url"),
                    usage_1y=raw.get("usage_character_count_1y") or 0,
                    usage_7d=raw.get("usage_character_count_7d") or 0,
                    cloned_by_count=raw.get("cloned_by_count") or 0,
                    free_users_allowed=bool(raw.get("free_users_allowed")),
                    verified_languages=raw.get("verified_languages") or [],
                )
            if not data.get("has_more"):
                break

    def add_shared_voice(self, public_owner_id: str, voice_id: str, new_name: str) -> str:
        """Add a shared-library voice to the user's account so it can be used for TTS.
        Returns the new local voice_id."""
        url = f"{BASE_URL}/v1/voices/add/{public_owner_id}/{voice_id}"
        r = self.session.post(url, json={"new_name": new_name}, timeout=30)
        if not r.ok:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
        time.sleep(self.request_delay)
        return r.json().get("voice_id")

    def tts(self, voice_id: str, text: str, model_id: str = DEFAULT_TTS_MODEL,
            output_format: str = "mp3_44100_128", language_code: str | None = None) -> bytes:
        """Generate speech. Returns raw audio bytes.
        Pass language_code (ISO 639-1) for non-English on eleven_v3."""
        url = f"{BASE_URL}/v1/text-to-speech/{voice_id}"
        payload: dict = {"text": text, "model_id": model_id}
        if language_code:
            payload["language_code"] = language_code
        r = self.session.post(
            url,
            params={"output_format": output_format},
            json=payload,
            headers={"Accept": "audio/mpeg"},
            timeout=60,
        )
        if not r.ok:
            raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
        time.sleep(self.request_delay)
        return r.content
