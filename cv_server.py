"""
Standalone Computer Vision Server for ContextSwitch
Runs on ws://127.0.0.1:8000/ws/cv with MediaPipe Head Tracking and Hand Gestures.
"""

import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "backend"))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from cv_service import CVService

cv_service = CVService(camera_index=0, show_preview=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    cv_service.set_loop(loop)
    cv_service.start_camera()
    dispatcher = asyncio.create_task(cv_service.event_dispatcher())
    print("[STANDALONE CV] Running on ws://127.0.0.1:8000/ws/cv")
    try:
        yield
    finally:
        cv_service.stop_camera()
        await dispatcher

app = FastAPI(title="ContextSwitch Standalone CV Server", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws/cv")
async def cv_ws(websocket):
    await cv_service.handle_websocket(websocket)

@app.get("/health")
def health():
    return cv_service.get_status()

if __name__ == "__main__":
    uvicorn.run("cv_server:app", host="127.0.0.1", port=8000, reload=False)
