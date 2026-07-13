"""Discover top Professional Voice Clones (PVC) in English on ElevenLabs shared library.
Sorts by 1-year usage volume (a strong proxy for quality/adoption).
Zero-credit operation."""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from providers.elevenlabs import ElevenLabsClient, SharedVoice

load_dotenv()

OUT_JSON = Path("candidates.json")
OUT_MD = Path("candidates.md")
PAGES_TO_SCAN = 20  # scan top 2000 PVCs
TOP_N_PER_GENDER = 15
FREE_USERS_ONLY = False  # Creator plan — all PVCs accessible


def row(v: SharedVoice) -> dict:
    return {
        "voice_id": v.voice_id,
        "public_owner_id": v.public_owner_id,
        "name": v.name,
        "gender": v.gender,
        "accent": v.accent,
        "age": v.age,
        "descriptive": v.descriptive,
        "use_case": v.use_case,
        "description": v.description[:140],
        "usage_1y": v.usage_1y,
        "cloned_by_count": v.cloned_by_count,
        "preview_url": v.preview_url,
    }


def main() -> None:
    client = ElevenLabsClient()
    print("Fetching top English PVCs from ElevenLabs shared library...")

    all_voices: list[SharedVoice] = list(
        client.iter_shared_voices(
            category="professional", language="en", max_pages=PAGES_TO_SCAN
        )
    )
    kept = all_voices if not FREE_USERS_ONLY else [v for v in all_voices if v.free_users_allowed]
    print(f"Scanned {len(all_voices)} PVC voices. {len(kept)} in shortlist pool.")

    by_gender: dict[str, list[SharedVoice]] = {"male": [], "female": []}
    for v in kept:
        if v.gender in by_gender:
            by_gender[v.gender].append(v)

    shortlist: dict[str, list[dict]] = {}
    for gender, voices in by_gender.items():
        voices.sort(key=lambda x: x.usage_1y, reverse=True)
        shortlist[gender] = [row(v) for v in voices[:TOP_N_PER_GENDER]]

    OUT_JSON.write_text(json.dumps(shortlist, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# ElevenLabs PVC candidates (English, sorted by 1y usage)",
        "",
        f"Top {TOP_N_PER_GENDER} per gender. Pick your final shortlist from these.",
        "Hebrew previews will be generated with the same voices via `eleven_multilingual_v2`.",
        "",
    ]
    for gender in ("female", "male"):
        lines.append(f"## {gender.capitalize()}")
        lines.append("")
        lines.append("| # | Name | Accent | Age | Descriptive | Use case | 1y usage (chars) | Clones | Voice ID |")
        lines.append("|---|------|--------|-----|-------------|----------|------------------|--------|----------|")
        for i, r in enumerate(shortlist[gender], 1):
            lines.append(
                f"| {i} | {r['name']} | {r['accent']} | {r['age']} | {r['descriptive']} | "
                f"{r['use_case']} | {r['usage_1y']:,} | {r['cloned_by_count']:,} | `{r['voice_id']}` |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_MD} and {OUT_JSON}")


if __name__ == "__main__":
    main()
