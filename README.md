# contextswitch

## Member 3 KiCad voice pipeline

The KiCad voice prototype is in `member3/`. It resolves known schematic entities, ranks templated commands with a local sentence embedding model, and escalates uncertain intents to Gemini. Gemini returns grounded candidates only; any Gemini-proposed action requires a local spoken confirmation and is revalidated by `ActionRouter.dispatch()`.

### Local setup

From `member3/`, create/activate a virtual environment and install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
```

Set `GEMINI_API_KEY` in the local `member3/.env`. That file is ignored by Git; never commit or paste the key into source. `GEMINI_MODEL` defaults to `gemini-3.8-flash`; `FASTEMBED_MODEL` defaults to `BAAI/bge-small-en-v1.5`.

### Commands

```sh
python -m unittest -v
python smoke_gemini.py
python calibrate_matcher.py
python voice_input.py --profile PCB_WEB --site KICAD_SCHEMATIC
```

The matcher threshold and margin are intentionally unset in `data/config/kicad_matcher.json`. Calibrate against the labeled phrases and accept a pair only when the calibration set has zero wrong accepts; otherwise leave the Gemini confirmation tier in place. The current action executor is still a mock: real KiCanvas focus/sheet actions and parsed KiCad connectivity/BOM data remain integration work.

