import json
from pathlib import Path
import unittest

from actions import Action, ActionRouter, MockExecutor, classify, parse_intent
from voice_input import process_transcript


class PhraseFixtureTests(unittest.TestCase):
    def test_phrase_fixtures(self):
        fixtures = json.loads((Path(__file__).with_name("phrase_fixtures.json")).read_text())
        for fixture in fixtures:
            with self.subTest(text=fixture["text"]):
                self.assertEqual(list(classify(fixture["text"])), fixture["expected"])


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.executor = MockExecutor()
        self.router = ActionRouter(self.executor)

    def test_typed_command_mock_loop(self):
        result = self.router.handle_text("scroll down", "DOCUMENTATION", "PDF", "scroll-1")
        self.assertTrue(result["success"])
        self.assertEqual(self.executor.executed[0].action, "SCROLL_DOWN")
        self.assertEqual(result["request_id"], "scroll-1")

    def test_complex_command_is_forwarded(self):
        result = self.router.handle_text("Show Motor 2's temperature", "MAINTENANCE", "INDUSTRIAL_DASHBOARD", "task-1")
        self.assertEqual(result["status"], "FORWARDED_TO_PLANNER")
        self.assertEqual(self.executor.executed, [])

    def test_dashboard_action_rejected_on_docs(self):
        action = Action("ACTION", "VOICE", "NEXT_PANEL", "MAINTENANCE", {}, "wrong-site")
        result = self.router.dispatch(action, "DOCUMENTATION")
        self.assertEqual(result["reason"], "UNSUPPORTED_PAGE")

    def test_unknown_action_and_bad_arguments_rejected(self):
        unknown = Action("ACTION", "VOICE", "EXECUTE_JS", "DOCUMENTATION", {}, "unknown")
        malformed = Action("ACTION", "AGENT", "SHOW_MACHINE", "MAINTENANCE", {"machine_id": 2}, "bad-arg")
        self.assertEqual(self.router.dispatch(unknown, "INDUSTRIAL_DASHBOARD")["reason"], "INVALID_ACTION")
        self.assertEqual(self.router.dispatch(malformed, "INDUSTRIAL_DASHBOARD")["reason"], "INVALID_ARGS")

    def test_pause_blocks_and_resume_restores_without_queueing(self):
        self.router.handle_text("pause", "DOCUMENTATION", "PDF", "pause-1")
        blocked = self.router.handle_text("scroll down", "DOCUMENTATION", "PDF", "blocked-1")
        self.assertEqual(blocked["reason"], "PAUSED")
        self.router.handle_text("resume", "DOCUMENTATION", "PDF", "resume-1")
        self.assertEqual(self.executor.executed, [])
        success = self.router.handle_text("scroll down", "DOCUMENTATION", "PDF", "scroll-2")
        self.assertTrue(success["success"])
        self.assertEqual(len(self.executor.executed), 1)

    def test_duplicate_request_is_not_executed_twice(self):
        first = self.router.handle_text("scroll down", "DOCUMENTATION", "PDF", "same-id")
        replay = self.router.handle_text("scroll down", "DOCUMENTATION", "PDF", "same-id")
        self.assertEqual(first, replay)
        self.assertEqual(len(self.executor.executed), 1)

    def test_agent_submission_requires_approval(self):
        action = Action("ACTION", "AGENT", "SUBMIT_FAULT_RECORD", "MAINTENANCE",
                        {"record_id": "draft-1", "approved": False}, "submit-1")
        result = self.router.dispatch(action, "INDUSTRIAL_DASHBOARD")
        self.assertEqual(result["reason"], "APPROVAL_REQUIRED")
        self.assertEqual(self.executor.executed, [])

    def test_kicad_voice_commands_produce_typed_actions(self):
        cases = [
            ("Locate J106, the USB connector", "LOCATE_COMPONENT", {"component_ref": "J106"}),
            ("Where is J108", "LOCATE_COMPONENT", {"component_ref": "J108"}),
            ("Find J 108", "LOCATE_COMPONENT", {"component_ref": "J108"}),
            ("Show me the J-108 connector", "LOCATE_COMPONENT", {"component_ref": "J108"}),
            ("Take me to J_108", "LOCATE_COMPONENT", {"component_ref": "J108"}),
            ("Where do USB D+ and D− go", "TRACE_SIGNAL", {"signal_name": "USB_P, USB_N"}),
            ("What's the purpose of R101", "EXPLAIN_COMPONENT", {"component_ref": "R101"}),
            ("Tell me about C 101", "EXPLAIN_COMPONENT", {"component_ref": "C101"}),
            ("Follow the I2C connections", "TRACE_SIGNAL", {"signal_name": "I2C"}),
            ("Open the 3.3-volt regulator", "OPEN_SHEET", {"sheet_id": "2_5Vto3.3VRegulator"}),
            ("Go to the SAMD21", "OPEN_SHEET", {"sheet_id": "3_uC_SAMD21"}),
            ("Switch to the SAMD21 sheet", "OPEN_SHEET", {"sheet_id": "3_uC_SAMD21"}),
            ("I'm assembling the USB section", "SHOW_ASSEMBLY_CHECKLIST", {"section_id": "USB"}),
            ("Show assembly checklist for USB section", "SHOW_ASSEMBLY_CHECKLIST", {"section_id": "USB"}),
            ("Check off C101", "MARK_COMPONENT_COMPLETE", {"component_ref": "C101"}),
            ("My board won't communicate over USB", "GUIDE_TROUBLESHOOTING", {"issue": "COMMUNICATE OVER USB"}),
            ("Display the USB area", "SHOW_SCHEMATIC_SECTION", {"section_id": "USB"}),
        ]
        for phrase, expected_action, expected_parameters in cases:
            with self.subTest(phrase=phrase):
                kind, action_name, parameters = parse_intent(phrase)
                self.assertEqual((kind, action_name, parameters), ("simple", expected_action, expected_parameters))

    def test_kicad_action_requires_kicad_profile_and_site(self):
        result = self.router.handle_text("Locate J106", "DOCUMENTATION", "PDF", "kicad-wrong-context")
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "UNSUPPORTED_PAGE")

    def test_kicad_voice_command_uses_router_result_path(self):
        result = self.router.handle_text("Locate J106", "PCB_WEB", "KICAD_SCHEMATIC", "locate-j106")
        self.assertTrue(result["success"])
        self.assertEqual(self.executor.executed[-1].parameters, {"component_ref": "J106"})

    def test_transcribed_voice_event_routes_and_has_timestamp(self):
        result = process_transcript(self.router, "Locate J106", "PCB_WEB", "KICAD_SCHEMATIC", "voice-1")
        self.assertEqual(result["voice_event"]["type"], "VOICE_EVENT")
        self.assertEqual(result["voice_event"]["status"], "TRANSCRIBED")
        self.assertIsInstance(result["voice_event"]["timestamp"], int)
        self.assertTrue(result["result"]["success"])
        self.assertEqual(self.executor.executed[-1].parameters, {"component_ref": "J106"})


if __name__ == "__main__":
    unittest.main()
