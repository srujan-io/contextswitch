# Member 3 — Voice & Action Execution Plan

**Project:** Beyond Touch 24-hour hackathon  
**Owner:** Member 3 (voice, action schema/router, website action execution)  
**Purpose:** Working checklist and running log. Update the checkboxes and append timestamped notes as work progresses. The first showcase target is now the KiCad schematic workflow described in `kicad.md`.

## Mission and definition of done

Deliver speech-to-text and deterministic routing for simple commands, a shared typed action vocabulary, safe validation against the active website/profile, and an execution/result path to the extension. By the demo, voice must trigger **two real browser actions**, and one agent-planned action must execute through the same validated path. Pause must block actions; duplicate requests must not execute twice.

## Order of work

### H0–H2 — Contracts and setup

- [ ] Sync with Member 4 (extension) and Member 2 (agent): freeze action names, request/result fields, transport/API route, and supported website for the first demo.
- [ ] Resolve the demo target with the team: the team context emphasizes Node-RED maintenance plus documentation; the timeline also calls for PDF navigation by H14 and PCB assembly at H14–H18. Build the smallest shared browser action layer first, then bind it to the agreed demo target. Do not build separate site integrations in parallel.
- [ ] Define the v1 action vocabulary, for example: `SCROLL_UP`, `SCROLL_DOWN`, `NEXT_PANEL`, `PREVIOUS_PANEL`, `SHOW_MACHINE`, `OPEN_GUIDE`, `PREPARE_FAULT_RECORD`, and `PAUSE`/`RESUME` if those are routed as actions.
- [ ] Define a typed action envelope consistent with the project contract: `type`, `source`, `action`, `profile`, `parameters`, `request_id`; define `ACTION_RESULT` with matching `request_id`, `success`, and user-readable `message`.
- [ ] Create a local/mock route for a voice command to yield an action and result, so progress does not wait on camera, Gemini, or the finished extension.

**Gate by H2:** teammates agree on names/route and a mock `SCROLL_DOWN` returns an action result.

### H2–H6 — Voice and deterministic command core

- [ ] Inspect the existing backend/repo structure; keep voice and action code in the agreed `backend/voice` and `backend/actions` (or existing equivalent) locations.
- [ ] Implement speech-to-text using the simplest available local/runtime option; expose a clean text input boundary so typed test commands work when a microphone or speech package is unavailable.
- [ ] Normalize recognized text (case, punctuation, common contractions) and route only clear simple intents deterministically: scroll up/down, next/previous panel, pause/resume.
- [ ] Send requests needing interpretation or domain knowledge (e.g. “show Motor 2’s temperature”, “prepare an overheating report”) to Member 2’s planner; do not send low-latency/simple controls through an LLM.
- [ ] Add unit-level/manual command fixtures for common phrases and ambiguous/unrecognized speech; ambiguous requests must ask/fail gracefully rather than guess a consequential action.

**Gate by H6:** voice or typed transcript produces a standardized action for at least scroll and panel navigation; complex intent is handed off rather than executed ad hoc.

### H6–H10 — Safe action router and real browser actions

- [ ] Implement an allowlist validator for action names, argument types/ranges, active profile, and supported site. Reject unknown actions and malformed arguments before dispatch.
- [ ] Add pause state and request deduplication by `request_id`; do not queue stale actions while paused or while the target tab/context is unavailable.
- [ ] Dispatch approved actions through Member 4’s backend/extension contract; rely on content-script DOM/site adapters, never screen coordinates or model-generated JavaScript.
- [ ] Work with Member 4 to make at least two actions visibly affect the real page (recommended: scroll and next/previous section/panel on the selected demo site).
- [ ] Return an `ACTION_RESULT` for success and failure, including unsupported page, disconnected extension, paused state, invalid input, and failed DOM target.
- [ ] Add a controlled agent-planned action path using the exact same validator and executor; read-only or navigational actions can execute, while record submission or other consequential changes require explicit approval.

**Gate by H10:** two real voice-triggered webpage actions work, duplicate requests are suppressed, and errors reach the UI.

### H10–H14 — MVP integration and PDF flow

- [ ] Integrate the voice command path with FastAPI/agent/extension end to end; verify request IDs and results survive the complete trip.
- [ ] Deliver the timeline’s complete hands-free PDF navigation flow by H14 if PDF is the agreed initial target; otherwise demonstrate equivalent supported-site navigation and record the PDF gap for the team.
- [ ] Confirm context/profile restrictions are enforced (e.g. a dashboard-only action is rejected on documentation/PDF pages).
- [ ] Verify pause blocks voice and agent-triggered actions and resume restores them intentionally.
- [ ] Give the team a short runbook: launch steps, supported voice phrases, expected page result, and fallback typed commands.

**Gate by H14:** integrated MVP is repeatable on the agreed target, with a working PDF navigation flow where that is the team’s chosen H14 scenario.

### H14–H18 — Industrial / PCB workflow binding

- [ ] Bind the shared action layer to the team’s selected H14–H18 scenario (timeline: PCB assembly; team context: Node-RED maintenance dashboard, with documentation as secondary).
- [ ] If PCB is selected, implement only the specific supported schematic navigation/component lookup/checklist actions agreed with the extension owner; do not imply arbitrary CAD control.
- [ ] If Node-RED is selected, support a real configured machine lookup/panel action and guide/fault draft preparation using actual demo data; do not invent telemetry.
- [ ] Ensure profile recommendation acceptance happens in the extension before profile-specific actions are enabled; never silently switch profiles.
- [ ] Keep `PREPARE_FAULT_RECORD` as draft preparation; gate any submit/change action on explicit user approval.

**Gate by H18:** one coherent domain workflow works from voice request through a grounded result or prepared draft.

### H18–H21 — Reliability and failure handling

- [ ] Try noisy/partial transcripts, no speech result, ambiguous command, repeated command, unavailable extension/backend, unsupported page, and rejected parameters.
- [ ] Verify emergency pause takes effect immediately, and no buffered command fires after resume.
- [ ] Exercise Gemini/API failure: simple commands still work deterministically; complex requests report a clear fallback/error.
- [ ] Fix highest-impact failures first; keep a manual/typed fallback and a reliable short list of demo phrases.

**Gate by H21:** no unsafe action under pause or invalid context; clear outcome for common failures; repeatable demo path.

### H21–H24 — Feature freeze and pitch support

- [ ] Freeze action names and features; make only demo-blocking fixes.
- [ ] Record backup demo and ensure seeded/simulated values are labeled accurately.
- [ ] Rehearse the voice portion in the three-minute script and confirm it works on the presentation laptop/microphone.
- [ ] Append final known limitations and fallback steps to this log.

**Gate by H24:** two real voice actions plus one safe agent-planned action shown in a short rehearsed demo, with a backup recording.

## Priorities if behind

1. Keep the real extension-to-page execution path and two real voice actions.
2. Keep pause, action validation, duplicate suppression, and visible success/failure.
3. Keep one agent-planned action on the same allowlisted execution path.
4. Complete one website workflow cleanly; defer extra sites, broad speech coverage, and optional features.

## Running work log

| Time (local) | Update |
|---|---|
| 2026-10-31 | Created plan from `BEYOND_TOUCH_TEAM_CONTEXT.md` and `hackathon-timeline.txt`. The sources differ on the initial/domain demo (PDF by H14; PCB vs. Node-RED at H14–H18), so the plan prioritizes shared action contracts and asks the team to select one target before site-specific work. |
| 2026-10-31 | Started the independent workflow. Added `member3/CONTRACT_PROPOSAL.md`, a dependency-free typed-command router and mock executor in `member3/actions.py`, phrase fixtures, and negative-path tests. Verified with `python3 -m unittest -v` in `member3/`: all 8 tests pass. The first fixture run caught punctuation normalization leaving a trailing space; fixed it and reran successfully. Workspace is not a Git repository, so there is no branch/commit available. Next: add a timestamped voice-event boundary/CLI and fake extension transport, then adapt the agreed shared contract after teammate sync. |
| 2026-10-31 | First showcase target set to KiCad based on `kicad.md`. Added KiCad action parsing and context validation to the mock router, documented the vocabulary and data-grounding constraints, and expanded verification. All 11 tests pass; real viewer/netlist/BOM integration remains. |
| 2026-10-31 | Added push-to-talk capture and timestamped voice-event routing in `member3/voice_input.py`; all 12 tests pass. Live capture currently requires PyAudio, which is missing here (Homebrew PortAudio is present). Speech transcription uses the Google Web Speech endpoint and requires network access. |
| 2026-10-31 | Expanded KiCad command phrase patterns and normalized component references with spoken gaps/separators (`J 108`, `J-108`, `J_108` → `J108`). Added variant fixtures and verified all 12 test methods pass in both source and local repository copy. |

### Append entries here

Use: `| YYYY-MM-DD HH:MM | What changed, what works, blockers, and next step. |`
