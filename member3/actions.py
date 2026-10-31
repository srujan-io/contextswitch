"""Member 3's dependency-free voice-to-action contract and mock router."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any
from uuid import uuid4


ACTION_RULES: dict[str, dict[str, Any]] = {
    "SCROLL_UP": {"parameters": {}, "profiles": {"DOCUMENTATION", "MAINTENANCE"}, "sites": {"PDF", "DOCUMENTATION", "INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "SCROLL_DOWN": {"parameters": {}, "profiles": {"DOCUMENTATION", "MAINTENANCE"}, "sites": {"PDF", "DOCUMENTATION", "INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "NEXT_PANEL": {"parameters": {}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "PREVIOUS_PANEL": {"parameters": {}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "NEXT_SECTION": {"parameters": {}, "profiles": {"DOCUMENTATION"}, "sites": {"PDF", "DOCUMENTATION"}, "consequential": False},
    "PREVIOUS_SECTION": {"parameters": {}, "profiles": {"DOCUMENTATION"}, "sites": {"PDF", "DOCUMENTATION"}, "consequential": False},
    "SHOW_MACHINE": {"parameters": {"machine_id": str}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "OPEN_GUIDE": {"parameters": {"fault_type": str}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD", "DOCUMENTATION"}, "consequential": False},
    "PREPARE_FAULT_RECORD": {"parameters": {"machine_id": str, "fault_type": str, "notes": str}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "SUBMIT_FAULT_RECORD": {"parameters": {"record_id": str, "approved": bool}, "profiles": {"MAINTENANCE"}, "sites": {"INDUSTRIAL_DASHBOARD"}, "consequential": True},
    "LOCATE_COMPONENT": {"parameters": {"component_ref": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "EXPLAIN_COMPONENT": {"parameters": {"component_ref": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "TRACE_SIGNAL": {"parameters": {"signal_name": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "OPEN_SHEET": {"parameters": {"sheet_id": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "RETURN_MAIN_SHEET": {"parameters": {}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "SHOW_ASSEMBLY_CHECKLIST": {"parameters": {"section_id": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "MARK_COMPONENT_COMPLETE": {"parameters": {"component_ref": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "GUIDE_TROUBLESHOOTING": {"parameters": {"issue": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "SHOW_SCHEMATIC_SECTION": {"parameters": {"section_id": str}, "profiles": {"PCB_WEB"}, "sites": {"KICAD_SCHEMATIC"}, "consequential": False},
    "PAUSE": {"parameters": {}, "profiles": {"DOCUMENTATION", "MAINTENANCE"}, "sites": {"PDF", "DOCUMENTATION", "INDUSTRIAL_DASHBOARD"}, "consequential": False},
    "RESUME": {"parameters": {}, "profiles": {"DOCUMENTATION", "MAINTENANCE"}, "sites": {"PDF", "DOCUMENTATION", "INDUSTRIAL_DASHBOARD"}, "consequential": False},
}


@dataclass(frozen=True)
class Action:
    type: str
    source: str
    action: str
    profile: str
    parameters: dict[str, Any]
    request_id: str


@dataclass(frozen=True)
class ActionResult:
    type: str
    request_id: str
    success: bool
    message: str
    reason: str | None = None


def normalize(text: str) -> str:
    value = text.lower().replace("’", "'").strip()
    value = re.sub(r"[^\w\s']", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.replace("don't", "do not")


def classify(text: str) -> tuple[str, str | None]:
    """Return (simple|complex|ambiguous|rejected, action name if simple)."""
    kind, name, _ = parse_intent(text)
    return kind, name


_COMPONENT_REF = r"(?:tp|[rcj])\s*[-_]?\s*\d{2,4}[a-z]?"


def canonical_component_ref(reference: str) -> str | None:
    """Join common ASR gaps and separators inside a KiCad reference only."""
    compact = re.sub(r"[\s_-]+", "", reference).upper()
    if re.fullmatch(r"(?:TP|[RCJ])\d{2,4}[A-Z]?", compact):
        return compact
    return None


def parse_intent(text: str) -> tuple[str, str | None, dict[str, Any]]:
    """Classify a transcript and extract typed arguments for supported commands."""
    value = normalize(text)
    # Preserve the generic navigation commands before the broader sheet parser.
    primary = {"go to next panel": "NEXT_PANEL", "next panel": "NEXT_PANEL",
               "previous panel": "PREVIOUS_PANEL", "go to previous panel": "PREVIOUS_PANEL"}
    if value in primary:
        return "simple", primary[value], {}
    # More than one natural phrase maps to each supported KiCad intent. Keep
    # identifier normalization local to references; don't rewrite normal text.
    patterns = [
        (rf"(?:locate|find|where is|where's|show me|focus on|take me to)\s+(?:the\s+)?(?:component\s+)?({_COMPONENT_REF})(?:\s+.*)?", "LOCATE_COMPONENT", "component_ref"),
        (rf"(?:what does|explain|describe|tell me about|what is the purpose of|what's the purpose of|purpose of|what is)\s+({_COMPONENT_REF})(?:\s+(?:do|used for))?", "EXPLAIN_COMPONENT", "component_ref"),
        (rf"(?:mark|set)\s+({_COMPONENT_REF})\s+(?:as\s+)?(?:complete|done)|(?:check off|complete|finish)\s+({_COMPONENT_REF})", "MARK_COMPONENT_COMPLETE", "component_ref"),
        (r"(?:trace|follow|track)\s+(?:the\s+)?(.+?)(?:\s+(?:signal|net|connections?))?$", "TRACE_SIGNAL", "signal_name"),
        (r"(?:open|go to|navigate to|switch to|show sheet)\s+(?:the\s+)?(.+?)(?:\s+sheet)?$", "OPEN_SHEET", "sheet_id"),
        (r"(?:i am|i'm|i am currently) assembling (?:the\s+)?(.+?)(?:\s+section)?$", "SHOW_ASSEMBLY_CHECKLIST", "section_id"),
        (r"(?:show|open|display) (?:the\s+)?(?:assembly )?checklist for (?:the\s+)?(.+?)(?:\s+section)?$", "SHOW_ASSEMBLY_CHECKLIST", "section_id"),
        (r"(?:my board (?:isn't|is not|won't|will not)|i (?:can't|cannot|am having trouble|have trouble)\s+with|troubleshoot|help me troubleshoot|help diagnose)\s+(.+)$", "GUIDE_TROUBLESHOOTING", "issue"),
        (r"(?:show me|show|open|display|focus on)\s+(?:the\s+)?(.+?)\s+(?:section|area|part)$", "SHOW_SCHEMATIC_SECTION", "section_id"),
    ]
    for pattern, action, parameter in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            captured = next((group for group in match.groups() if group), "")
            argument = captured.strip().upper()
            if parameter == "component_ref":
                canonical = canonical_component_ref(captured)
                if not canonical:
                    continue
                argument = canonical
            if parameter == "sheet_id":
                aliases = {
                    "THE 3 3 VOLT REGULATOR": "2_5Vto3.3VRegulator",
                    "3 3 VOLT REGULATOR": "2_5Vto3.3VRegulator",
                    "THE SAMD21": "3_uC_SAMD21",
                    "SAMD21": "3_uC_SAMD21",
                }
                argument = aliases.get(argument, argument)
            if action == "SHOW_ASSEMBLY_CHECKLIST":
                argument = argument.removesuffix(" SECTION").strip()
            return "simple", action, {parameter: argument}
    signal_match = re.fullmatch(r"where do (.+) go", value)
    if signal_match:
        signal = signal_match.group(1).upper()
        if "USB" in signal:
            signal = "USB_P, USB_N"
        return "simple", "TRACE_SIGNAL", {"signal_name": signal}
    if value in {"return to the main schematic", "return to main schematic", "go back to the main schematic",
                 "go back to main schematic", "return to root schematic", "back to the root schematic",
                 "open the main schematic", "take me back to the main schematic"}:
        return "simple", "RETURN_MAIN_SHEET", {}
    exact = {
        "scroll down": "SCROLL_DOWN", "scroll down please": "SCROLL_DOWN", "page down": "SCROLL_DOWN",
        "scroll up": "SCROLL_UP", "scroll up please": "SCROLL_UP", "page up": "SCROLL_UP",
        "next panel": "NEXT_PANEL", "go to next panel": "NEXT_PANEL", "previous panel": "PREVIOUS_PANEL",
        "previous panel please": "PREVIOUS_PANEL", "next section": "NEXT_SECTION", "previous section": "PREVIOUS_SECTION",
        "pause": "PAUSE", "pause controls": "PAUSE", "resume": "RESUME", "resume controls": "RESUME",
    }
    if value in exact:
        return "simple", exact[value], {}
    if not value or value in {"blah blah", "gibberish", "asdf"}:
        return "rejected", None, {}
    if value in {"go next", "move", "do it", "stop", "scroll", "next"}:
        return "ambiguous", None, {}
    complex_markers = ("temperature", "motor", "machine", "fault", "overheat", "guide", "report", "troubleshoot")
    if any(word in value for word in complex_markers):
        return "complex", None, {}
    return "rejected", None, {}


class MockExecutor:
    """A local stand-in for the extension; records executions for dedup checks."""

    def __init__(self) -> None:
        self.executed: list[Action] = []

    def execute(self, action: Action) -> ActionResult:
        self.executed.append(action)
        return ActionResult("ACTION_RESULT", action.request_id, True, f"Mock executed {action.action}")


class ActionRouter:
    def __init__(self, executor: MockExecutor | None = None) -> None:
        self.executor = executor or MockExecutor()
        self.paused = False
        self.results: dict[str, ActionResult] = {}

    def handle_text(self, text: str, profile: str, site_type: str, request_id: str | None = None) -> dict[str, Any]:
        kind, action_name, parameters = parse_intent(text)
        if kind == "complex":
            return {"type": "VOICE_EVENT", "text": text, "status": "FORWARDED_TO_PLANNER"}
        if kind != "simple":
            return asdict(ActionResult("ACTION_RESULT", request_id or str(uuid4()), False,
                                       "Command was not clear enough to execute", kind.upper()))
        return self.dispatch(Action("ACTION", "VOICE", action_name or "", profile, parameters, request_id or str(uuid4())), site_type)

    def dispatch(self, action: Action, site_type: str) -> dict[str, Any]:
        if action.request_id in self.results:
            return asdict(self.results[action.request_id])
        result: ActionResult
        rule = ACTION_RULES.get(action.action)
        if not rule:
            result = ActionResult("ACTION_RESULT", action.request_id, False, "Action is not allowed", "INVALID_ACTION")
        elif set(action.parameters) != set(rule["parameters"]) or any(
            not isinstance(action.parameters.get(k), typ) or (typ is int and isinstance(action.parameters.get(k), bool))
            for k, typ in rule["parameters"].items()
        ):
            result = ActionResult("ACTION_RESULT", action.request_id, False, "Action arguments are invalid", "INVALID_ARGS")
        elif action.profile not in rule["profiles"] or site_type not in rule["sites"]:
            result = ActionResult("ACTION_RESULT", action.request_id, False, "Action is not supported in this profile or website", "UNSUPPORTED_PAGE")
        elif self.paused and action.action != "RESUME":
            result = ActionResult("ACTION_RESULT", action.request_id, False, "Controls are paused", "PAUSED")
        elif rule["consequential"] and action.parameters.get("approved") is not True:
            result = ActionResult("ACTION_RESULT", action.request_id, False, "User approval is required", "APPROVAL_REQUIRED")
        elif action.action == "PAUSE":
            self.paused = True
            result = ActionResult("ACTION_RESULT", action.request_id, True, "Controls paused")
        elif action.action == "RESUME":
            self.paused = False
            result = ActionResult("ACTION_RESULT", action.request_id, True, "Controls resumed")
        else:
            result = self.executor.execute(action)
        self.results[action.request_id] = result
        return asdict(result)
