# Member 3 Code Explanations

## How the files fit together

- `member3/CONTRACT_PROPOSAL.md` describes the proposed action/result format and the allowed actions. It is the design reference; names still need agreement with the integration teammates.
- `member3/actions.py` implements the current standalone voice-to-action path. `classify()` recognizes simple commands, identifies complex requests for planner handoff, and marks unclear input as ambiguous or rejected. `ActionRouter` validates actions and returns structured results. `MockExecutor` stands in for the browser extension and records successful mock executions.
- `member3/voice_input.py` provides push-to-talk microphone capture, speech transcription, timestamped voice events, and calls `ActionRouter` with the transcript. `member3/requirements.txt` declares its speech/audio packages.
- `member3/phrase_fixtures.json` lists example speech transcripts and their expected classifications.
- `member3/test_actions.py` reads those fixtures and checks classification, routing, validation, pause/resume, duplicate suppression, planner handoff, and approval gating.
- `per_session_summary.md` records implementation progress and next steps. `wholeplan.md` tracks the wider hackathon plan and phase progress.

## KiCad showcase actions

The initial KiCad voice list is represented by `LOCATE_COMPONENT`, `EXPLAIN_COMPONENT`, `TRACE_SIGNAL`, `OPEN_SHEET`, `RETURN_MAIN_SHEET`, `SHOW_ASSEMBLY_CHECKLIST`, `MARK_COMPONENT_COMPLETE`, `GUIDE_TROUBLESHOOTING`, and `SHOW_SCHEMATIC_SECTION`. These require profile `PCB_WEB` and site type `KICAD_SCHEMATIC`. Multiple common phrases map to each intent (for example, “where is,” “find,” or “show me” map to component location). Component references are normalized locally, so `J 108`, `J-108`, and `J108` become `J108`. The parser extracts values such as `J106`, `USB_P, USB_N`, and the canonical SAMD21 sheet ID. The current executor remains a mock; real focus/navigation, netlist tracing, grounded explanations, and checklist persistence still need a KiCad viewer/data adapter.

## Chronological command flow

1. A transcript is passed to `ActionRouter.handle_text()` (currently the input can be typed; microphone speech-to-text is not yet connected).
2. `parse_intent()` normalizes the text, matches supported phrases, and extracts typed parameters. `classify()` exposes only the intent category/name for fixture checks. Ambiguous or unrecognized phrases return a failure result without dispatching an action.
3. A simple phrase becomes an `Action` containing its source, action name, active profile, parameters, and request ID.
4. `dispatch()` checks the action allowlist, required argument types, supported profile/site, pause state, and any explicit approval requirement.
5. `PAUSE` and `RESUME` update router state. Other valid actions go to `MockExecutor`, which returns an `ACTION_RESULT`. Repeated request IDs return their saved result instead of executing twice.
6. The tests drive this flow with fixed phrases and fake context. They verify the current local behavior without requiring FastAPI, a microphone, Gemini, or the extension.

## Current integration boundary

The action executor remains local/mock and does not yet cause real KiCad viewer actions. Microphone capture requires PyAudio and OS microphone access. Transcription currently uses SpeechRecognition's Google Web Speech endpoint, so it needs network access and sends recorded audio to that service. The tests cover transcript routing, not live audio recognition. The proposed contract guides later integration with the planner and KiCad viewer adapter.
