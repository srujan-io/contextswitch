"""Push-to-talk speech recognition wired to the Member 3 action router.

Recognition uses SpeechRecognition's Google Web Speech backend. Audio is sent
to that service; use typed input instead when network recognition is unwanted
or unavailable. PyAudio is needed for live microphone capture.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
import sys
import time
from typing import Any
from uuid import uuid4

from actions import ActionRouter


@dataclass(frozen=True)
class VoiceEvent:
    type: str
    source: str
    text: str
    status: str
    timestamp: int


def process_transcript(router: ActionRouter, text: str, profile: str, site_type: str,
                       request_id: str | None = None) -> dict[str, Any]:
    """Pass recognized text through the same deterministic route as typed text."""
    event = VoiceEvent("VOICE_EVENT", "VOICE", text, "TRANSCRIBED", int(time.time() * 1000))
    result = router.handle_text(text, profile, site_type, request_id or str(uuid4()))
    return {"voice_event": asdict(event), "result": result}


def listen_once(profile: str, site_type: str, language: str = "en-US",
                device_index: int | None = None, timeout: float = 5,
                phrase_time_limit: float = 8, router: ActionRouter | None = None) -> dict[str, Any]:
    """Record one push-to-talk utterance and route its transcript."""
    try:
        import speech_recognition as sr
    except ImportError as exc:
        return _unavailable("SpeechRecognition is missing. Install member3/requirements.txt.", exc)

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone(device_index=device_index) as microphone:
            print("Listening briefly for ambient noise...")
            recognizer.adjust_for_ambient_noise(microphone, duration=0.4)
            print("Speak your command now.")
            audio = recognizer.listen(microphone, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        return _status("UNCERTAIN", "No speech detected before timeout")
    except (AttributeError, OSError) as exc:
        return _unavailable("Microphone capture is unavailable. Install PyAudio and check microphone access.", exc)

    try:
        transcript = recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return _status("UNCERTAIN", "Speech was not clear enough to transcribe")
    except sr.RequestError as exc:
        return _unavailable("Speech recognition service is unavailable; use typed input or retry.", exc)

    return process_transcript(router or ActionRouter(), transcript, profile, site_type)


def _status(status: str, message: str) -> dict[str, Any]:
    return {"voice_event": asdict(VoiceEvent("VOICE_EVENT", "VOICE", "", status, int(time.time() * 1000))),
            "result": {"type": "VOICE_STATUS", "success": False, "message": message}}


def _unavailable(message: str, exc: Exception) -> dict[str, Any]:
    result = _status("UNAVAILABLE", message)
    result["result"]["detail"] = str(exc)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Member 3 push-to-talk voice command demo")
    parser.add_argument("--profile", default="PCB_WEB")
    parser.add_argument("--site", default="KICAD_SCHEMATIC")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--device-index", type=int,
                        default=int(os.environ["BEYOND_TOUCH_MIC_INDEX"]) if os.environ.get("BEYOND_TOUCH_MIC_INDEX") else None)
    parser.add_argument("--once", action="store_true", help="Run one microphone capture and exit")
    args = parser.parse_args(argv)

    router = ActionRouter()
    while True:
        try:
            input("Press Enter to talk (Ctrl+C to quit): ")
        except EOFError:
            return 0
        except KeyboardInterrupt:
            print()
            return 0
        result = listen_once(args.profile, args.site, args.language, args.device_index, router=router)
        event = result.get("voice_event", {})
        if event.get("status") != "TRANSCRIBED":
            try:
                fallback = input("Type a fallback command (blank to retry): ").strip()
            except EOFError:
                fallback = ""
            if fallback:
                result = {"type": "TEXT_FALLBACK", "text": fallback,
                          "result": router.handle_text(fallback, args.profile, args.site)}
        print(json.dumps(result, indent=2))
        if args.once or (event.get("status") == "UNAVAILABLE" and not fallback):
            return 0 if event.get("status") == "TRANSCRIBED" else 1


if __name__ == "__main__":
    sys.exit(main())
