"""
Voice Service Bridge for ContextSwitch
Connects Member 3 voice recognition, ground truth resolver, and semantic matcher
to the KiCanvas execution manager and browser extension.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

# Ensure member3 is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
MEMBER3_DIR = ROOT_DIR / "member3"
if str(MEMBER3_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER3_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from actions import ActionRouter, Action, ACTION_RULES
    from pipeline import build_default_pipeline
    from resolver import GroundTruthResolver
    from voice_status import VoiceStatusMonitor
    from settings import load_settings
except ImportError as err:
    print(f"[VOICE] Warning: member3 module import error: {err}")
    ActionRouter = None


class VoiceService:
    def __init__(self, action_validator=None, execution_manager=None, context_store=None):
        self.action_validator = action_validator
        self.execution_manager = execution_manager
        self.context_store = context_store
        self.router = None
        self.monitor = None
        self.history = []
        self._initialize_router()

    def _initialize_router(self):
        try:
            settings = load_settings()
            self.monitor = VoiceStatusMonitor(settings)
            pipeline = build_default_pipeline()
            self.router = ActionRouter(
                intent_pipeline=pipeline,
                resolver=pipeline.resolver
            )
            print("[VOICE] KiCad Voice Intent Pipeline and Matcher initialized successfully.")
        except Exception as exc:
            print(f"[VOICE] Falling back to rule-based ActionRouter: {exc}")
            try:
                self.router = ActionRouter()
            except Exception as e2:
                print(f"[VOICE] ActionRouter initialization error: {e2}")

    def get_status(self) -> dict[str, Any]:
        metadata = self.monitor.metadata() if self.monitor else {
            "quality": "GOOD",
            "noise_level": "LOW",
            "failure_count_in_window": 0,
            "reason": "OK"
        }
        return {
            "status": "ready" if self.router else "degraded",
            "profile": "PCB_WEB",
            "site_type": "KICAD_SCHEMATIC",
            "metadata": metadata,
            "recent_commands_count": len(self.history)
        }

    def map_to_kicanvas_action(self, voice_action: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
        """
        Maps KiCad Member 3 voice actions to browser-executed KiCanvas skill actions.
        """
        action_name = voice_action.upper()
        if action_name in ("LOCATE_COMPONENT", "SEARCH_COMPONENT"):
            ref = parameters.get("component_ref") or parameters.get("query") or ""
            return {
                "action": "search_component",
                "target": "component_search",
                "parameters": {"query": str(ref).upper().strip()}
            }
        elif action_name == "ZOOM_IN":
            return {
                "action": "zoom_in",
                "target": "schematic_canvas",
                "parameters": {}
            }
        elif action_name == "ZOOM_OUT":
            return {
                "action": "zoom_out",
                "target": "schematic_canvas",
                "parameters": {}
            }
        elif action_name in ("SCROLL_UP", "PAN_UP"):
            return {
                "action": "pan",
                "target": "schematic_canvas",
                "parameters": {"direction": "up"}
            }
        elif action_name in ("SCROLL_DOWN", "PAN_DOWN"):
            return {
                "action": "pan",
                "target": "schematic_canvas",
                "parameters": {"direction": "down"}
            }
        elif action_name in ("PREVIOUS_PANEL", "PAN_LEFT", "PREVIOUS_SECTION"):
            return {
                "action": "pan",
                "target": "schematic_canvas",
                "parameters": {"direction": "left"}
            }
        elif action_name in ("NEXT_PANEL", "PAN_RIGHT", "NEXT_SECTION"):
            return {
                "action": "pan",
                "target": "schematic_canvas",
                "parameters": {"direction": "right"}
            }
        elif action_name in ("EXPLAIN_COMPONENT", "VIEW_COMPONENT_DETAILS"):
            ref = parameters.get("component_ref") or parameters.get("reference") or ""
            return {
                "action": "view_component_details",
                "target": "component",
                "parameters": {"reference": str(ref).upper().strip()}
            }
        elif action_name == "TRACE_SIGNAL":
            sig = parameters.get("signal_name") or ""
            return {
                "action": "trace_signal",
                "target": "signal",
                "parameters": {"signal_name": str(sig).upper().strip()}
            }
        return None

    def process_command(
        self,
        transcript: str,
        tab_id: int | None = None,
        profile: str = "PCB_WEB",
        site_type: str = "KICAD_SCHEMATIC",
        auto_dispatch: bool = True
    ) -> dict[str, Any]:
        """
        Process a voice transcript, parse into KiCad action, map to KiCanvas,
        and automatically dispatch to the active tab queue.
        """
        clean_text = transcript.strip()
        if not clean_text:
            return {"status": "error", "message": "Empty voice transcript."}

        # 1. Route voice text through Member 3 router
        decision_raw = None
        action_name = None
        parameters = {}
        source = "VOICE"

        if self.router:
            decision_raw = self.router.handle_text(clean_text, profile=profile, site_type=site_type)
            pipeline_details = getattr(self.router, "last_pipeline_details", {})
            source = pipeline_details.get("source", "RULE")
            
            # Extract action and parameters if recognized
            if decision_raw.get("success"):
                action_name = pipeline_details.get("parsed_action")
                parameters = dict(pipeline_details.get("parameters") or {})
                if not parameters and hasattr(self.router, "last_dispatched_action") and self.router.last_dispatched_action:
                    parameters = dict(getattr(self.router.last_dispatched_action, "parameters", {}) or {})
                # Fallback to action string if parsed
                if not action_name and "message" in decision_raw:
                    msg = decision_raw["message"]
                    if "Mock executed" in msg:
                        action_name = msg.replace("Mock executed", "").strip()

            elif decision_raw.get("reason") == "CONFIRMATION_REQUIRED":
                proposal = decision_raw.get("proposal", {})
                action_name = proposal.get("action")
                parameters = dict(proposal.get("parameters", {}) or {})

        # Fallback keyword & reference extraction if parameters missing component_ref
        import re
        if action_name in ("LOCATE_COMPONENT", "EXPLAIN_COMPONENT", "MARK_COMPONENT_COMPLETE") and not parameters.get("component_ref"):
            m = re.search(r"\b([a-zA-Z]{1,3}\s*\d{1,4}[a-zA-Z]?)\b", clean_text)
            if m:
                parameters["component_ref"] = m.group(1).replace(" ", "").upper()

        if not action_name:
            lower = clean_text.lower()
            if "zoom in" in lower:
                action_name = "ZOOM_IN"
            elif "zoom out" in lower:
                action_name = "ZOOM_OUT"
            elif "pan up" in lower or "scroll up" in lower:
                action_name = "SCROLL_UP"
            elif "pan down" in lower or "scroll down" in lower:
                action_name = "SCROLL_DOWN"
            elif "pan left" in lower or "previous" in lower:
                action_name = "PREVIOUS_PANEL"
            elif "pan right" in lower or "next" in lower:
                action_name = "NEXT_PANEL"
            elif any(w in lower for w in ("locate", "find", "where is", "show component")):
                m = re.search(r"\b([a-zA-Z]{1,3}\s*\d{1,4}[a-zA-Z]?)\b", clean_text)
                if m:
                    action_name = "LOCATE_COMPONENT"
                    parameters = {"component_ref": m.group(1).replace(" ", "").upper()}

        # 2. Map to KiCanvas skill action
        mapped = self.map_to_kicanvas_action(action_name or "", parameters) if action_name else None

        # 3. Determine active KiCanvas tab
        active_tab_id = tab_id
        active_context = None
        if self.context_store:
            active_ctx = self.context_store.get_active()
            if active_ctx and "tab_id" in active_ctx:
                active_context = active_ctx
                if active_tab_id is None:
                    active_tab_id = active_ctx.get("tab_id")

        dispatched = False
        job_info = None

        # 4. Auto-dispatch action to execution manager for active tab
        if auto_dispatch and mapped and active_tab_id and self.action_validator and self.execution_manager:
            plan = {
                "website": "kicanvas",
                "intent": f"Voice Command: {clean_text}",
                "steps": [mapped]
            }
            try:
                validation = self.action_validator.validate_plan(
                    plan=plan,
                    context=active_context or {"website_id": "kicanvas", "page_type": "schematic_viewer"},
                    user_approved=True
                )
                if validation.get("valid") and validation.get("execution_ready"):
                    job_info = self.execution_manager.submit(
                        tab_id=active_tab_id,
                        validated=validation
                    )
                    dispatched = True
            except Exception as e:
                print(f"[VOICE] Auto-dispatch failed: {e}")

        record = {
            "id": str(uuid4())[:8],
            "transcript": clean_text,
            "action": action_name,
            "parameters": parameters,
            "mapped_action": mapped,
            "source": source,
            "dispatched": dispatched,
            "tab_id": active_tab_id,
            "job": job_info
        }
        self.history.append(record)
        if len(self.history) > 50:
            self.history.pop(0)

        return {
            "status": "success",
            "transcript": clean_text,
            "voice_decision": decision_raw,
            "action_name": action_name,
            "parameters": parameters,
            "mapped_action": mapped,
            "dispatched": dispatched,
            "tab_id": active_tab_id,
            "job": job_info
        }
