"""Generate ElevenLabs preview clips.
Folder structure: output/elevenlabs/<language>/<gender>/<voice_name>.mp3
Reads shortlist_elevenlabs.json. Appends to manifest.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

from dotenv import load_dotenv

from languages import LANGUAGES
from providers.elevenlabs import ElevenLabsClient

load_dotenv(override=True)

ROOT = Path(__file__).parent
OUTPUT = ROOT / "output"
SHORTLIST = ROOT / "shortlist_elevenlabs.json"
MANIFEST = ROOT / "manifest.json"


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

    client = ElevenLabsClient()
    manifest = [m for m in load_manifest() if m.get("provider") != provider]

    for v in voices:
        gender = v["gender"]
        name = v["name"]
        voice_id = v["voice_id"]
        public_owner_id = v["public_owner_id"]

        if public_owner_id:
            try:
                local_voice_id = client.add_shared_voice(
                    public_owner_id=public_owner_id,
                    voice_id=voice_id,
                    new_name=f"HS-{slug(name)}"[:100],
                )
                print(f"[+] Added shared voice {name} -> {local_voice_id}")
            except Exception as e:
                print(f"[i] add_shared_voice for {name}: {e}. Using original voice_id.")
                local_voice_id = voice_id
        else:
            # premade or already-owned voice — use voice_id directly
            local_voice_id = voice_id
            print(f"[i] Using premade/owned voice: {name}")

        for lang_code, text in v["sentences"].items():
            out_dir = OUTPUT / provider / lang_code / gender
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{slug(name)}.mp3"

            lang_hint = lang_code if lang_code != "en" else None
            print(f"    -> {lang_code} ({len(text)} chars): {out_path.relative_to(ROOT)}")
            audio = client.tts(voice_id=local_voice_id, text=text, model_id=model_id, language_code=lang_hint)
            out_path.write_bytes(audio)

            manifest.append({
                "provider": provider,
                "model_id": model_id,
                "voice_name": name,
                "voice_id": voice_id,
                "local_voice_id": local_voice_id,
                "gender": gender,
                "language": lang_code,
                "language_name": LANGUAGES[lang_code]["name"],
                "category": v.get("category", ""),
                "accent": v.get("accent", ""),
                "age": v.get("age", ""),
                "use_case": v.get("use_case", ""),
                "text": text,
                "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            })

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. {len([m for m in manifest if m['provider']==provider])} ElevenLabs clips. Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
