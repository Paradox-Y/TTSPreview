"""Generate report.md — a single comparison table across all providers."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
MANIFEST = ROOT / "manifest.json"
REPORT = ROOT / "report.md"


def main() -> None:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # Collect all voice names and build a pivot: voice -> {provider/lang -> file}
    voices: dict[str, dict] = {}
    for e in entries:
        key = f"{e['provider']}::{e['voice_name']}"
        if key not in voices:
            voices[key] = {
                "provider": e["provider"],
                "model_id": e["model_id"],
                "voice_name": e["voice_name"],
                "gender": e["gender"],
                "category": e.get("category", ""),
                "accent": e.get("accent", "") or e.get("country", ""),
                "age": e.get("age", ""),
                "use_case": e.get("use_case", "") or e.get("description", "")[:60],
                "clips": {},
            }
        lang = e["language"]
        voices[key]["clips"][lang] = e["file"]

    lines = [
        "# TTS Voice Preview Report — Hyper Sales",
        "",
        "Sentence used — **EN:** \"Hi! Thanks for reaching out to Hyper Sales. How can we help you today?\"",
        "Sentence used — **HE:** \"היי! תודה שפניתם להייפר סיילס. איך נוכל לעזור?\"",
        "",
    ]

    for provider_label, provider_id in [("ElevenLabs (`eleven_v3`)", "elevenlabs"),
                                         ("Cartesia (`sonic-3.5`)", "cartesia")]:
        lines.append(f"## {provider_label}")
        lines.append("")

        for gender in ("female", "male"):
            lines.append(f"### {gender.capitalize()}")
            lines.append("")
            lines.append("| Voice | Category | Accent | Age | Use case | EN preview | HE preview |")
            lines.append("|-------|----------|--------|-----|----------|------------|------------|")
            for v in voices.values():
                if v["provider"] != provider_id or v["gender"] != gender:
                    continue
                clips = v["clips"]
                en_link = f"[▶ EN]({clips['en']})" if "en" in clips else "—"
                he_link = f"[▶ HE]({clips['he']})" if "he" in clips else "—"
                cat = "⭐ PVC" if v["category"] == "professional" else v["category"]
                lines.append(
                    f"| **{v['voice_name']}** | {cat} | {v['accent']} | {v['age']} | "
                    f"{v['use_case']} | {en_link} | {he_link} |"
                )
            lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT} ({len(entries)} clips, {len(voices)} voices)")


if __name__ == "__main__":
    main()
