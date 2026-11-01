"""
ContextSwitch - Unified Workstation Launcher
Runs the complete unified backend (API, CV WebSocket, Voice Pipeline, and Light-Mode Lab UI)
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
MEMBER3_DIR = ROOT_DIR / "member3"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(MEMBER3_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER3_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.chdir(str(BACKEND_DIR))

if __name__ == "__main__":
    import uvicorn
    print("=" * 65)
    print("[*] Starting ContextSwitch Multimodal Electronics Lab Workstation")
    print("=" * 65)
    print(" - Electronics Lab UI:  http://127.0.0.1:8001/demo")
    print(" - REST Context API:    http://127.0.0.1:8001")
    print(" - CV WebSocket:        ws://127.0.0.1:8001/ws/cv")
    print(" - Extension Directory: " + str(ROOT_DIR / "extension"))
    print("=" * 65)
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)
