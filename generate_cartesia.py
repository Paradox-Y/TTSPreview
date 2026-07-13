"""Generate Cartesia preview clips.
Cartesia voices are language-specialized — each voice generates its native language.
Folder structure: output/cartesia/<language>/<gender>/<voice_name>.mp3
Reads shortlist_cartesia.json. Appends to manifest.json (dedupes cartesia entries)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from dotenv import load_dotenv

from languages import LANGUAGES
from providers.cartesia import CartesiaClient

load_dotenv(override=True)

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
SHORTLIST = ROOT / "shortlist_cartesia.json"
MANIFEST = ROOT / "manifest.json"

# Cartesia uses feminine/masculine; keep folder naming consistent with ElevenLabs.
GENDER_TO_FOLDER = {"feminine": "female", "masculine": "male", "gender_neutral": "neutral"}


def slug(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"[\s-]+", "-", s)


def load_manifest() -> list[dict]:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def main() -> None:
    shortlist = json.loads(SHORTLIST.read_text(encoding="utf-8"))
    provider = shortlist["provider"]
    model_id = shortlist["model_id"]
    voices = shortlist["voices"]

    client = CartesiaClient()
    manifest = [m for m in load_manifest() if m.get("provider") != provider]

    for v in voices:
        cartesia_gender = v["gender"]
        folder_gender = GENDER_TO_FOLDER.get(cartesia_gender, cartesia_gender)
        name = v["name"]
        voice_id = v["id"]
        lang_code = v["language"]

        text = v["sentences"][lang_code]

        out_dir = OUTPUT / provider / lang_code / folder_gender
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug(name)}.mp3"

        print(f"[i] {name} ({lang_code}/{folder_gender}, {len(text)} chars)")
        print(f"    -> {out_path.relative_to(ROOT)}")
        audio = client.tts(voice_id=voice_id, transcript=text, language=lang_code, model_id=model_id)
        out_path.write_bytes(audio)

        manifest.append({
            "provider": provider,
            "model_id": model_id,
            "voice_name": name,
            "voice_id": voice_id,
            "gender": folder_gender,
            "cartesia_gender": cartesia_gender,
            "language": lang_code,
            "language_name": LANGUAGES[lang_code]["name"],
            "country": v.get("country", ""),
            "description": v.get("description", ""),
            "text": text,
            "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
        })

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. {len([m for m in manifest if m['provider']==provider])} Cartesia clips. Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
