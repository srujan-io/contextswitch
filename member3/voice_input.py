"""Push-to-talk speech recognition wired to the Member 3 action router.

Recognition uses SpeechRecognition's Google Web Speech backend. Audio is sent
there; use typed input instead when network recognition is unwanted or unavailable.
PyAudio is needed for microphone capture; NumPy measures non-speech ambient RMS.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
import os
import sys
import time
from typing import Any
from uuid import uuid4

from actions import ActionRouter
from settings import load_settings
from voice_status import STATUS_OUTPUT_LOCK, VoiceStatusMonitor, VoiceStatusReporter


@dataclass(frozen=True)
class VoiceEvent:
    type: str
    source: str
    text: str
    status: str
    timestamp: int
    metadata: dict[str, Any]


def process_transcript(router: ActionRouter, text: str, profile: str, site_type: str,
                       request_id: str | None = None,
                       status_monitor: VoiceStatusMonitor | None = None) -> dict[str, Any]:
    """Pass a non-empty recognized transcript through the action router."""
    monitor = status_monitor or VoiceStatusMonitor(load_settings())
    if not text.strip():
        monitor.record_asr_failure("ASR_EMPTY_RESULT")
        event = _make_voice_event("UNCERTAIN", "", monitor)
        return {"voice_event": asdict(event),
                "result": {"type": "VOICE_STATUS", "success": False,
                           "message": "Speech recognition returned an empty transcript"}}

    monitor.record_asr_success()
    event = _make_voice_event("TRANSCRIBED", text, monitor)
    result = router.handle_text(text, profile, site_type, request_id or str(uuid4()))
    return {"voice_event": asdict(event), "result": result}


def listen_once(profile: str, site_type: str, language: str = "en-US",
                device_index: int | None = None, timeout: float = 5,
                phrase_time_limit: float = 8, router: ActionRouter | None = None,
                status_monitor: VoiceStatusMonitor | None = None) -> dict[str, Any]:
    """Capture one ambient sample and one utterance, then transcribe and route it."""
    monitor = status_monitor or VoiceStatusMonitor(load_settings())
    try:
        import speech_recognition as sr
    except ImportError as exc:
        monitor.mark_unavailable("SPEECH_RECOGNITION_MISSING")
        return _unavailable("SpeechRecognition is missing. Install member3/requirements.txt.", exc, monitor)

    try:
        recognizer = sr.Recognizer()
        with sr.Microphone(device_index=device_index) as microphone:
            print("Measuring ambient noise briefly...")
            ambient_rms = _measure_ambient_rms(microphone, duration=0.4)
            monitor.observe_noise(ambient_rms)
            # SpeechRecognition uses frame RMS against energy_threshold; retain
            # its dynamic ratio while calibrating from the current ambient sample.
            recognizer.energy_threshold = max(50.0, ambient_rms * recognizer.dynamic_energy_ratio)
            print("Speak your command now.")
            audio = recognizer.listen(microphone, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except sr.WaitTimeoutError:
        monitor.record_asr_failure("NO_SPEECH_TIMEOUT")
        return _status("UNCERTAIN", "No speech detected before timeout", monitor)
    except ImportError as exc:
        monitor.mark_unavailable("NUMPY_RMS_UNAVAILABLE")
        return _unavailable("NumPy RMS measurement is unavailable. Install member3/requirements.txt.", exc, monitor)
    except (AttributeError, OSError, ValueError) as exc:
        monitor.mark_unavailable("MIC_UNAVAILABLE")
        return _unavailable("Microphone capture is unavailable. Check PyAudio and microphone access.", exc, monitor)

    try:
        transcript = recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        monitor.record_asr_failure("ASR_UNRECOGNIZED")
        return _status("UNCERTAIN", "Speech was not clear enough to transcribe", monitor)
    except sr.RequestError as exc:
        monitor.record_asr_failure("ASR_NETWORK_ERROR")
        return _unavailable("Speech recognition service is unavailable; you can type a command or retry.", exc, monitor)

    return process_transcript(router or ActionRouter(), transcript, profile, site_type,
                              status_monitor=monitor)


def _measure_ambient_rms(source: Any, duration: float) -> float:
    """Measure NumPy RMS over a pre-utterance, non-speech PCM interval."""
    import numpy as np

    import numpy as np

    chunk_size = int(source.CHUNK)
    sample_rate = int(source.SAMPLE_RATE)
    chunk_count = max(1, math.ceil(duration * sample_rate / chunk_size))
    chunks = []
    width = int(source.SAMPLE_WIDTH)
    for _ in range(chunk_count):
        data = source.stream.read(chunk_size)
        if width == 1:
            samples = np.frombuffer(data, dtype=np.uint8).astype(np.float64) - 128.0
        elif width == 2:
            samples = np.frombuffer(data, dtype="<i2").astype(np.float64)
        elif width == 3:
            raw = np.frombuffer(data[:len(data) - len(data) % 3], dtype=np.uint8).reshape(-1, 3)
            values = raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int32) << 16)
            samples = ((values ^ 0x800000) - 0x800000).astype(np.float64)
        elif width == 4:
            samples = np.frombuffer(data, dtype="<i4").astype(np.float64)
        else:
            raise ValueError(f"Unsupported microphone sample width: {width}")
        if samples.size:
            chunks.append(samples)
    if not chunks:
        return 0.0
    samples = np.concatenate(chunks)
    return float(np.sqrt(np.mean(np.square(samples))))


def _make_voice_event(status: str, text: str, monitor: VoiceStatusMonitor) -> VoiceEvent:
    return VoiceEvent("VOICE_EVENT", "VOICE", text, status,
                      int(time.time() * 1000), monitor.metadata())


def _status(status: str, message: str, monitor: VoiceStatusMonitor) -> dict[str, Any]:
    event = _make_voice_event(status, "", monitor)
    return {"voice_event": asdict(event),
            "result": {"type": "VOICE_STATUS", "success": False, "message": message}}


def _unavailable(message: str, exc: Exception, monitor: VoiceStatusMonitor) -> dict[str, Any]:
    event = _make_voice_event("UNAVAILABLE", "", monitor)
    result = {"type": "VOICE_STATUS", "success": False, "message": message,
              "detail": f"{type(exc).__name__}"}
    return {"voice_event": asdict(event), "result": result}


def _print_json(payload: dict[str, Any]) -> None:
    with STATUS_OUTPUT_LOCK:
        print(json.dumps(payload, indent=2), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Member 3 push-to-talk voice command demo")
    parser.add_argument("--profile", default="PCB_WEB")
    parser.add_argument("--site", default="KICAD_SCHEMATIC")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--device-index", type=int,
                        default=int(os.environ["BEYOND_TOUCH_MIC_INDEX"]) if os.environ.get("BEYOND_TOUCH_MIC_INDEX") else None)
    parser.add_argument("--once", action="store_true", help="Run one microphone capture and exit")
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
    except Exception as exc:
        print(f"Voice settings unavailable ({type(exc).__name__}). Check Member 3 configuration.", file=sys.stderr)
        return 1

    monitor = VoiceStatusMonitor(settings)
    reporter = VoiceStatusReporter(monitor)
    reporter.start()
    try:
        from pipeline import build_default_pipeline
        from session_logger import SessionLogger
        intent_pipeline = build_default_pipeline()
        router = ActionRouter(intent_pipeline=intent_pipeline, resolver=intent_pipeline.resolver,
                              session_logger=SessionLogger())
        print("KiCad intent pipeline initialized; unmatched commands will use semantic routing.")
    except Exception as exc:
        monitor.mark_unavailable("INTENT_PIPELINE_UNAVAILABLE")
        print(f"Could not initialize KiCad intent pipeline ({type(exc).__name__}).", file=sys.stderr)
        reporter.stop()
        return 1

    try:
        while True:
            try:
                input("Press Enter to talk (Ctrl+C to quit): ")
            except EOFError:
                return 0
            except KeyboardInterrupt:
                print()
                return 0
            result = listen_once(args.profile, args.site, args.language, args.device_index,
                                 router=router, status_monitor=monitor)
            event = result.get("voice_event", {})
            if event.get("status") != "TRANSCRIBED":
                try:
                    fallback = input("Type a fallback command (blank to retry): ").strip()
                except EOFError:
                    fallback = ""
                except KeyboardInterrupt:
                    print()
                    return 0
                if fallback:
                    result = {"type": "TEXT_FALLBACK", "text": fallback,
                              "result": router.handle_text(fallback, args.profile, args.site)}
            _print_json(result)
            if args.once:
                return 0 if event.get("status") == "TRANSCRIBED" else 1
    finally:
        reporter.stop()


if __name__ == "__main__":
    raise SystemExit(main())
