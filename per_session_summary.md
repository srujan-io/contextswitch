# Member 3 — Ongoing Session Log

Project-relevant implementation notes, in chronological order. This log tracks what each coding step changed and how it affects the Beyond Touch voice/action path.

## 2026-10-31 — Independent action path foundation

### Step 1 — Defined a provisional shared action contract

Added `member3/CONTRACT_PROPOSAL.md` to document the proposed `ACTION` and `ACTION_RESULT` fields, action vocabulary, parameter types, supported profiles/site types, and failure codes. The contract is explicitly provisional until Members 2 and 4 agree on names and transport.

### Step 2 — Implemented deterministic text classification

Added `member3/actions.py` with text normalization and a deterministic intent table for scroll, panel/section navigation, and pause/resume phrases. Complex domain requests are marked `FORWARDED_TO_PLANNER`; ambiguous and unrecognized commands do not execute.

### Step 3 — Built the standalone action router and mock executor

The router validates actions against an allowlist, including exact argument keys/types and profile/site support. It returns structured `ACTION_RESULT` payloads. The mock executor records executions so the command-to-result loop can be exercised without the extension or backend integration.

### Step 4 — Added pause, deduplication, and approval gates

Pause blocks new actions; resume re-enables controls without replaying blocked commands. Duplicate `request_id` values return the saved result without re-executing. `SUBMIT_FAULT_RECORD` requires explicit approval; preparing a record remains a separate draft action.

### Step 5 — Added command fixtures and negative-path tests

Added `member3/phrase_fixtures.json` for simple, complex, ambiguous, and rejected phrases, and `member3/test_actions.py` for routing, unsupported site/profile, malformed/unknown actions, pause/resume, duplicate IDs, planner handoff, and approval requirements.

### Step 6 — Ran and corrected the initial verification

Ran `python3 -m unittest -v` from `member3/`. The first run found punctuation normalization left a trailing space for a punctuated phrase. Updated normalization to trim after punctuation removal, then reran: **8 tests passed**.

## Current implementation boundary

- Implemented: push-to-talk text routing, deterministic fast controls, KiCad target resolver, local sentence-embedding matcher, Gemini candidate interpreter, confirmation state, profile/site/entity validation, pause/resume, deduplication, and JSONL diagnostics.
- Still blocked/unverified: third-party dependency installation and live Gemini/embedding calls; score thresholds are intentionally uncalibrated; real KiCad viewer actions still use the mock executor.
- The local API key is stored only in ignored `contextswitch/member3/.env`; no key value is logged or committed.

## Next code steps

1. Restore package/API network access, install `member3/requirements.txt`, and run `smoke_gemini.py`.
2. Run `calibrate_matcher.py` with the actual FastEmbed model; set thresholds only if the labeled calibration set has zero wrong accepts.
3. Replace `MockExecutor` with the agreed KiCad viewer adapter and verify one real component/sheet action.
4. Push the two local branch commits after GitHub DNS/auth is available.

## 2026-10-31 — KiCad showcase action mapping

### Step 7 — Mapped the KiCad voice list to typed actions

Read `kicad.md` and added actions for component location/explanation, signal tracing, hierarchical sheet navigation, assembly checklist display/progress, and guided troubleshooting. Added deterministic phrase patterns and extracted fields such as component reference, signal name, and sheet ID. KiCad actions require `PCB_WEB` plus `KICAD_SCHEMATIC`; other contexts reject them.

### Step 8 — Added KiCad fixtures and router coverage

Extended phrase fixtures and tests with showcase utterances, typed parameter extraction, context rejection, and mock dispatch. Overlapping patterns initially classified panel navigation as sheet navigation, and punctuation/captured trailing words affected component phrases; corrected those cases. `python3 -m unittest -v` from `member3/` passes **11 tests**.

### Step 9 — Updated contract and code explanation

Documented the KiCad action vocabulary and grounding requirements. The mock does not yet integrate with schematic viewer controls, parsed netlist/BOM data, or persistent checklist state.

## 2026-10-31 — Push-to-talk speech input

### Step 10 — Added microphone transcription and router integration

Added `member3/voice_input.py` with a push-to-talk microphone capture, ambient-noise calibration, configurable language/device, timestamped `VOICE_EVENT`, and routing through the existing action router. The CLI preserves pause/dedup state across utterances, supports retry after uncertain speech, and stops with a clear status when microphone or recognition service is unavailable. `member3/requirements.txt` declares SpeechRecognition with its audio extra.

### Step 11 — Verified text/event flow and checked microphone availability

Added a test that sends a transcribed KiCad command through the router and checks the event timestamp and typed action. `python3 -m unittest -v` passes **12 tests**. Live microphone check reports `UNAVAILABLE`: SpeechRecognition is present, but PyAudio is missing in this environment. PortAudio is installed via Homebrew; install the declared Python audio dependency and grant microphone access to use capture. Recognition uses the Google Web Speech endpoint, so the transcript step requires network access and sends recorded audio to that service. Typed commands remain usable without it.

## 2026-10-31 — Expanded KiCad phrase matching

Added natural variants for component locate/explain, sheet navigation, signal tracing, checklist display/progress, troubleshooting, and section navigation. Component references accept embedded spaces, hyphens, and underscores and are canonicalized (e.g. `J 108`, `J-108`, and `J_108` become `J108`). Added fixture and parameter-extraction cases. All 12 test methods pass in both the working tree and local `contextswitch/member3` copy. Parser remains deterministic; it does not use sentence embeddings.

## 2026-10-31 — Gemini + embedding pipeline stages

### Stage 0 — Credential and SDK setup

Added `contextswitch/.gitignore` before copying the uploaded local key into `member3/.env`; verified that path is ignored and that Git history contains no commit for the key file path. `settings.py` is the only runtime environment loader. Configured the current stable Flash model from official Google documentation. Attempted dependency installation in the project virtual environment; package index DNS is unavailable, so `google-genai`, `fastembed`, and `python-dotenv` are not installed here. The smoke command now fails safely without printing exception details or credentials.

### Stage 1 — KiCad ground truth and action catalog

Added `data/kicad_ground_truth.json`, `data/catalogs/kicad.json`, and 90 labeled examples (10 per KiCad action plus negatives). Entries are based only on `kicad.md`; there was no actual schematic/BOM/netlist available to cross-check details.

### Stage 2 — Resolver

Added `resolver.py` for known refs/synonyms, `J 108` and spoken homophone forms, conservative fuzzy resolution, placeholder templating, unknown-target failures, and the `J108`/USB descriptor contradiction check. Added tests including `J999` and `go to sleep`.

### Stage 3 — Sentence matcher and calibration

Added a FastEmbed adapter, in-memory catalog vector priming, cosine ranking, score/margin gates, labeled dataset, and `calibrate_matcher.py`. The threshold and margin remain null with `calibrated=false`; the script could not be run because FastEmbed/model downloads are blocked by DNS. The matcher therefore cannot auto-accept uncalibrated scores.

### Stage 4 — Gemini interpreter

Added structured candidate generation via the Google GenAI SDK, with active-catalog enum, transcript evidence checks, resolver-grounded arguments, ambiguity handling, a small cache, and API failure fallback. Mocked tests reject hallucinated target values/actions and test candidate validation. A live API call could not run because package installation/network access is unavailable.

### Stage 5 — Router orchestration

Integrated fast control commands, resolve/match/Gemini stages, one expiring confirmation proposal, local `yes` handling, pause cancellation, and final revalidation through `dispatch()`. Gemini candidates do not execute directly.

### Stage 6 — Per-utterance logging

Added local JSONL logging for transcript, template, match scores, escalation trigger, Gemini candidates, and final result; log directory is Git-ignored. The logger does not record API credentials or prompts.

**Verification:** `python3 -m unittest -v` from `contextswitch/member3/`: **34 tests pass**. Python syntax compilation passes. Live Gemini and FastEmbed calibration remain blocked until dependencies/network are available. Real KiCad UI actions also remain behind the mock executor.

### Branch state after initial pipeline integration

Committed the initial integration as `a09fc7b` on local `kicad_voicecommands`; at that point the branch was two commits ahead of `origin`. A push attempt failed because this environment could not resolve `github.com`. No `.env` file was staged.

## 2026-10-31 — Gemini smoke check troubleshooting

Created `contextswitch/member3/.venv` and attempted to install `requirements.txt` inside it. The install cannot reach PyPI because DNS resolution is unavailable, so the requirements set could not be installed there. The local environment now has `google-genai` available, but a repeated smoke attempt fails before receiving an HTTP response with DNS `ConnectError`; the user's earlier `ClientError` could not be reproduced while DNS was down. The `.env` exists with a configured key/model (values not logged). Improved the smoke script to report HTTP/status details and sanitized API error messages when available, without printing key material or headers. Ran the full suite in the project venv: **35 tests pass**. Next: restore DNS/network access, install remaining dependencies, and rerun the smoke check to capture the actual API status; live Gemini behavior is still unverified.

### Timeout fix

The user-provided API response identified the actual client error: Gemini rejects the configured 3-second deadline and requires at least 10 seconds. Updated `settings.py` to use `GEMINI_TIMEOUT_MS = 10000` and added a guard test. The suite now passes **36 tests** and the module compiles. The smoke command in this environment still stops at DNS `ConnectError`, so the 10-second request has not been live-verified here.

## Append format

For each session, append a dated section with: **step**, **code/project change**, **verification/result**, and **next step/blocker**. Keep entries focused on implementation and integration details.
