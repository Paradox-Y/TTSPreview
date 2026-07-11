# Task: ElevenLabs Voice Preview Generator — Hyper Sales

## Goal

Build a script (Python ) that pulls voice metadata from the ElevenLabs API and generates Hebrew + English preview audio clips for a shortlist of voices, organized into a clean folder structure. Must be built so new languages can be added later without restructuring. Also in the futuer we will add cartesia
And also we will have diffrent sentences for each langues and each voice. But all the sentences will be simular: Short and represanting meaning we can understand quicky how the voice sounds
so the folder should be something like this
Model (11labs/Cartesia) -> Language -> Male/Female
And we will also have a table with all the data for each file like this

## Context

This is for evaluating TTS voices for Hyper Sales, a B2B voice AI sales/support platform (LiveKit-based voice agent stack). We need to compare voice quality across languages before picking a default voice per language for our agents.

Examples of a line to read (You will have to genrate many other):
"Hey my name is Mika, and i can help you with anything you need!"
"היי, אני אבי ואני םה לעזור לך במה שצריך"

## Pull voice metadata

For each voice ID above, call the ElevenLabs `/v1/voices` (or `/v2/voices` — check current docs, this may have changed) endpoint and extract:

- `voice_id`
- `name`
- `category` (premade / professional / cloned / generated — this is the authoritative "Professional Voice Clone" flag)
- `labels` (gender, accent, age, description, use case — whatever is present)
- default `preview_url`

## Step 4 — Output report

Generate a `report.md` at the project root that's a single table: voice name, gender, category (flag Professional Voice Clones clearly), and relative file paths to all generated previews per language, so it's easy to scan and compare.

## Notes / constraints

- ElevenLabs API key: use environment variable, do not hardcode.
- Rate limit gracefully — don't blast all requests in parallel, add small delays or a concurrency cap.
- Check current ElevenLabs API docs before implementing (endpoints/params may have changed since your training data) — don't guess at request/response shapes.
- Keep the script modular enough that adding a new language later = just adding a language file + rerunning, and adding a new model later = a new provider module without touching the folder logic for existing ones.
