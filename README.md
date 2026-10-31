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

Set `GEMINI_API_KEY` in the local `member3/.env`. That file is ignored by Git; never commit or paste the key into source. `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite`; `FASTEMBED_MODEL` defaults to `BAAI/bge-small-en-v1.5`.

### Commands

```sh
python -m unittest -v
python smoke_gemini.py
python calibrate_matcher.py
python calibrate_voice_noise.py
python voice_input.py --profile PCB_WEB --site KICAD_SCHEMATIC
```

`calibrate_voice_noise.py` records five seconds of quiet-room audio and five seconds with fan/music noise. Choose the RMS ratio cutoffs from those measurements, then set `VOICE_NOISE_BASELINE_RMS`, `VOICE_NOISE_LOW_MAX_RATIO`, `VOICE_NOISE_MED_MAX_RATIO`, `VOICE_NOISE_ENTER_RATIO`, `VOICE_NOISE_EXIT_RATIO`, and `VOICE_THRESHOLDS_CALIBRATED=true` in `member3/.env`. Until a valid calibrated configuration is present, status events report `noise_level: UNKNOWN` and `noise_ratio: null`. Repeat calibration with Windows microphone noise suppression both enabled and disabled when applicable.

The voice process emits a `STATUS` JSON event at startup, on metadata changes, and every five seconds. It also appends status events to `member3/data/logs/voice_status.jsonl`. `failure_count_in_window` counts ASR failures in the configured last-N-attempt window; a single unrecognized utterance does not move `quality` out of `GOOD`. `UNAVAILABLE` is immediate for microphone or PyAudio failures. ASR network failures are reported with an ASR-specific reason, logged, and do not stop the normal voice loop.

The matcher threshold and margin are intentionally unset in `data/config/kicad_matcher.json`. Calibrate against the labeled phrases and accept a pair only when the calibration set has zero wrong accepts; otherwise leave the Gemini confirmation tier in place. The current action executor is still a mock: real KiCanvas focus/sheet actions and parsed KiCad connectivity/BOM data remain integration work.

