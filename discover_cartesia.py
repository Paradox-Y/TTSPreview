"""Discover Cartesia voices with native Hebrew + English support.
Zero-credit operation (metadata only)."""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from providers.cartesia import CartesiaClient, CartesiaVoice

load_dotenv(override=True)

OUT_JSON = Path("candidates_cartesia.json")
OUT_MD = Path("candidates_cartesia.md")


def row(v: CartesiaVoice) -> dict:
    return {
        "id": v.id,
        "name": v.name,
        "gender": v.gender,
        "language": v.language,
        "country": v.country,
        "is_pro": v.is_pro,
        "description": v.description[:160],
        "preview_file_url": v.preview_file_url,
    }


def main() -> None:
    client = CartesiaClient()

    result: dict[str, dict[str, list[dict]]] = {"he": {"feminine": [], "masculine": []},
                                                "en": {"feminine": [], "masculine": []}}

    for lang in ("he", "en"):
        for gender in ("feminine", "masculine"):
            voices = list(client.iter_voices(language=lang, gender=gender, max_pages=3))
            print(f"language={lang} gender={gender}: {len(voices)} voices")
            # Prefer is_pro=True first, then rest — pro flag is Cartesia's PVC equivalent
            voices.sort(key=lambda v: (not v.is_pro, v.name.lower()))
            result[lang][gender] = [row(v) for v in voices]

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Cartesia voice candidates",
        "",
        "Hebrew is natively supported by Sonic 3.5 — voices tagged `language=he` are trained/tuned for Hebrew.",
        "",
    ]
    for lang, label in [("he", "Hebrew"), ("en", "English")]:
        lines.append(f"## {label} (`language={lang}`)")
        lines.append("")
        for gender in ("feminine", "masculine"):
            lines.append(f"### {gender.capitalize()}")
            lines.append("")
            lines.append("| # | Name | Pro? | Country | Description | Voice ID |")
            lines.append("|---|------|------|---------|-------------|----------|")
            for i, r in enumerate(result[lang][gender], 1):
                lines.append(
                    f"| {i} | {r['name']} | {'✅' if r['is_pro'] else ''} | "
                    f"{r['country'] or ''} | {r['description']} | `{r['id']}` |"
                )
            lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_MD} and {OUT_JSON}")


if __name__ == "__main__":
    main()
