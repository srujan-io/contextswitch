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

- Implemented: typed text input, deterministic routing, proposed action schema, local fake execution/result path, profile/site/action validation, pause/resume, deduplication, and submission approval check.
- Not yet implemented: microphone speech-to-text, timestamped/transported voice events, WebSocket fake extension client, real browser DOM actions, or teammate contract integration.
- The first showcase now targets KiCad. The parser supports the voice workflows in `kicad.md`, but demo-specific viewer/data integration is still pending.

## Next code steps

1. Add a small CLI/text boundary around the router for repeatable local demos.
2. Add timestamped standardized voice events while preserving deterministic handling of simple commands.
3. Add a fake extension WebSocket client/result loop once the backend transport choice is set (or keep it transport-neutral until then).
4. Sync the proposed schema/action names with Members 2 and 4 before binding to shared endpoints.

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

## Append format

For each session, append a dated section with: **step**, **code/project change**, **verification/result**, and **next step/blocker**. Keep entries focused on implementation and integration details.
