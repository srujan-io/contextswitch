# Member 3 Code Explanations

## How the files fit together

- `member3/CONTRACT_PROPOSAL.md` describes the proposed action/result format and the allowed actions. It is the design reference; names still need agreement with the integration teammates.
- `member3/actions.py` implements the current standalone voice-to-action path. `classify()` recognizes simple commands, identifies complex requests for planner handoff, and marks unclear input as ambiguous or rejected. `ActionRouter` validates actions and returns structured results. `MockExecutor` stands in for the browser extension and records successful mock executions.
- `member3/voice_input.py` provides push-to-talk microphone capture, speech transcription, timestamped voice events, and calls `ActionRouter` with the transcript. `member3/requirements.txt` declares its speech/audio packages.
- `member3/data/kicad_ground_truth.json` contains the supported component, signal, sheet, section, and issue facts. `member3/data/catalogs/kicad.json` supplies example sentences for matching; it does not authorize actions.
- `member3/resolver.py` canonicalizes component references, resolves targets, templates entities, and rejects unknown or contradictory component references.
- `member3/matcher.py` embeds catalog examples once per process and ranks a transcript template. It will not auto-accept until both calibrated threshold and margin are explicitly enabled.
- `member3/interpreter.py` sends only uncertain requests to Gemini. It checks action membership, transcript evidence, and resolved parameters; it proposes candidates but never runs them.
- `member3/pipeline.py` coordinates resolution, embedding ranking, and Gemini escalation. `settings.py` is the single place that loads the ignored `.env` and creates the Gemini client.
- `member3/calibrate_matcher.py` scores labeled phrases and reports threshold/margin candidates with zero wrong accepts. `smoke_gemini.py` checks the Gemini and local embedding dependencies.
- `member3/session_logger.py` writes transcript, decision diagnostics, candidates, and final result to a local ignored JSONL log. It does not log the key or model prompt.
- `member3/phrase_fixtures.json` lists example speech transcripts and their expected classifications.
- `member3/test_actions.py` reads those fixtures and checks classification, routing, validation, pause/resume, duplicate suppression, planner handoff, and approval gating.
- `per_session_summary.md` records implementation progress and next steps. `wholeplan.md` tracks the wider hackathon plan and phase progress.

## KiCad showcase actions

The initial KiCad voice list is represented by `LOCATE_COMPONENT`, `EXPLAIN_COMPONENT`, `TRACE_SIGNAL`, `OPEN_SHEET`, `RETURN_MAIN_SHEET`, `SHOW_ASSEMBLY_CHECKLIST`, `MARK_COMPONENT_COMPLETE`, `GUIDE_TROUBLESHOOTING`, and `SHOW_SCHEMATIC_SECTION`. These require profile `PCB_WEB` and site type `KICAD_SCHEMATIC`. Multiple common phrases map to each intent. Component references accept spoken spacing and homophones such as `J 108`, `J-108`, `jay one oh eight`, and `J108`; they resolve to a known component or fail safely. Facts in the ground-truth file are limited to `kicad.md`; no real schematic/netlist/BOM file was supplied for independent verification.

## Chronological command flow

1. Push-to-talk speech recognition transcribes a phrase and emits a timestamped `VOICE_EVENT`; typed input remains a fallback.
2. `ActionRouter` handles fixed scroll/pause/navigation commands directly. Other KiCad requests go through `IntentPipeline`.
3. `GroundTruthResolver` resolves entities and detects unknown references or contradictions, then replaces targets with placeholders for matching.
4. `EmbeddingMatcher` scores the template against the KiCad catalog. The current score thresholds are unset, so embedding scores cannot directly dispatch actions yet.
5. On a matcher trigger, `GeminiInterpreter` returns up to three grounded candidates. If a candidate passes code-side checks, the router stores one short-lived proposal and asks for confirmation.
6. A spoken “yes” dispatches the proposal through the normal allowlist, entity, profile/site, pause, and dedup checks. Pause clears pending confirmation. Gemini never directly executes actions.
7. `MockExecutor` still stands in for KiCad viewer actions. The JSONL logger records diagnostics and outcome locally without credentials.

Mock tests cover the fast path, resolver, matcher thresholds, Gemini candidate validation, confirmation, pause, and failure handling. They do not confirm live API access or real KiCad page actions.

## Current integration boundary

The executor remains local/mock and does not yet cause real KiCad viewer actions. Dependency installation and the live Gemini smoke check could not run because this environment cannot resolve package/Gemini hosts; the current virtual environment lacks `google-genai` and `fastembed`. Keep thresholds unset until the labeled phrases are scored with the real embedding model and calibration yields zero wrong accepts.
