
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# --------------------------------------------------
# MODULE A — CONTEXT DETECTION
# --------------------------------------------------

from context.detector import enrich_context
from context.state import ContextStore

# --------------------------------------------------
# MODULE B — WEBSITE SKILL ROUTING
# --------------------------------------------------

from skills.router import WebsiteSkillRouter

# --------------------------------------------------
# MODULE C — INTENT AND PLANNING
# --------------------------------------------------

from planner.schemas import PlannerRequest
from planner.agent import IntentPlanner

# --------------------------------------------------
# MODULE D — ACTION VALIDATION
# --------------------------------------------------

from validation.action_validator import (
    ActionValidator,
    ValidationRequest,
)

# --------------------------------------------------
# MODULE E — ACTION EXECUTION
# --------------------------------------------------

from execution.manager import execution_manager
from execution.schemas import (
    DispatchRequest,
    ExecutionResultRequest,
)

# --------------------------------------------------
# MODULE F & G — CV & VOICE SERVICES + DEMO UI
# --------------------------------------------------

from cv_service import CVService
from voice_service import VoiceService
from demo_ui import get_demo_html


# ==================================================
# 1. INITIALIZE MODULES & LIFESPAN
# ==================================================

store = ContextStore()
skill_router = WebsiteSkillRouter()
planner = IntentPlanner(skill_router)
action_validator = ActionValidator(
    skill_router=skill_router,
    max_steps=5,
)

cv_service = CVService(camera_index=0, show_preview=False)
voice_service = VoiceService(
    action_validator=action_validator,
    execution_manager=execution_manager,
    context_store=store
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    cv_service.set_loop(loop)
    cv_service.start_camera()
    dispatcher_task = asyncio.create_task(cv_service.event_dispatcher())

    print("[SERVER] BeyondTouch Unified Backend started on http://127.0.0.1:8001")
    print("[SERVER] Electronics Lab Dashboard available at http://127.0.0.1:8001/demo")
    print("[SERVER] CV WebSocket available at ws://127.0.0.1:8001/ws/cv")

    try:
        yield
    finally:
        cv_service.stop_camera()
        await dispatcher_task


# ==================================================
# 2. CREATE FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Beyond Touch Context & Lab API",
    description=(
        "Context detection, KiCanvas skill routing, "
        "Computer Vision gestures, Voice processing, and Action execution."
    ),
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# 3. ELECTRONICS LAB DEMO UI & HEALTH
# ==================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/demo", response_class=HTMLResponse)
def get_lab_demo_page():
    """Serves the elegant light-mode electronics lab workstation UI."""
    return HTMLResponse(content=get_demo_html())


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Beyond Touch unified backend is running.",
        "active_tab": store.get_active().get("tab_id"),
        "cv": cv_service.get_status(),
        "voice": voice_service.get_status(),
    }



# ==================================================
# 4. MODULE A — CONTEXT ENDPOINTS
# ==================================================

@app.post("/context/update")
def update_context(context: dict):
    tab_id = context.get("tab_id")

    if tab_id is None:
        raise HTTPException(
            status_code=400,
            detail="tab_id is missing from context."
        )

    try:
        if isinstance(tab_id, bool) or not isinstance(tab_id, (int, str)):
            raise ValueError
        tab_id = int(tab_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="tab_id must be an integer.")

    enriched = enrich_context(context)
    enriched["tab_id"] = tab_id
    store.update(tab_id, enriched)

    return {
        "status": "success",
        "context": enriched
    }

@app.get("/context/active")
def get_active_context():
    """
    Returns the context of the currently active tab.
    """

    context = store.get_active()

    if context.get("message") == "No active context yet.":
        raise HTTPException(
            status_code=404,
            detail="No active context found.",
        )

    return context


@app.get("/context/active/{tab_id}")
def get_context_for_tab(tab_id: int):
    """
    Returns the stored context for a particular tab.
    """

    context = store.get(tab_id)

    if context.get("message") == "No context for this tab yet.":
        raise HTTPException(
            status_code=404,
            detail="Context not found for this tab.",
        )

    return context


@app.post("/context/activate/{tab_id}")
def activate_context(tab_id: int):
    """
    Sets a previously registered tab as active.
    """

    context = store.get(tab_id)

    if context.get("message") == "No context for this tab yet.":
        raise HTTPException(
            status_code=404,
            detail="Context not found for this tab.",
        )

    store.set_active(tab_id)

    return {
        "status": "success",
        "tab_id": tab_id,
        "context": store.get_active(),
    }


@app.delete("/context/remove/{tab_id}")
def remove_context(tab_id: int):
    """
    Removes a tab's stored context.
    """

    store.remove(tab_id)

    return {
        "status": "success",
        "tab_id": tab_id,
    }


# ==================================================
# 5. MODULE B — WEBSITE SKILL ROUTING
# ==================================================

@app.post("/skills/active")
def get_active_skill(context: dict):
    """
    Returns the actions supported by the current website
    and page type.
    """

    website_id = context.get("website_id")
    page_type = context.get("page_type")

    if not website_id:
        raise HTTPException(
            status_code=400,
            detail="website_id is required.",
        )

    if not page_type:
        raise HTTPException(
            status_code=400,
            detail="page_type is required.",
        )

    skill = skill_router.get_skill(website_id)

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="No skill found for this website.",
        )

    return skill.describe()


@app.post("/skills/validate-action")
def validate_skill_action(request: dict):
    """
    Checks whether an individual action is supported
    by the website skill.
    """

    website_id = request.get("website_id")
    page_type = request.get("page_type")
    action = request.get("action")
    parameters = request.get("parameters", {})
    target = request.get("target")

    if not website_id or not page_type or not action:
        raise HTTPException(
            status_code=400,
            detail=(
                "website_id, page_type and action "
                "are required."
            ),
        )

    if not isinstance(parameters, dict):
        raise HTTPException(
            status_code=400,
            detail="parameters must be an object.",
        )

    skill = skill_router.get_skill(website_id)

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Website skill not found.",
        )

    try:
        result = skill_router.validate_action(
            context={"website_id": website_id, "page_type": page_type},
            action=action,
            target=target,
            parameters=parameters,
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


# ==================================================
# 6. MODULE C — INTENT AND PLANNING
# ==================================================

@app.post("/planner/create-plan")
def create_plan(request: PlannerRequest):
    """
    Converts a natural-language command into
    a structured action plan.
    """

    try:
        return planner.create_plan(
            command=request.command,
            context=request.context,
            page_metadata=request.page_metadata,
            session_state=request.session_state,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Planner error: {str(error)}",
        )


# ==================================================
# 7. MODULE D — ACTION VALIDATION
# ==================================================

@app.post("/actions/validate")
def validate_action(request: ValidationRequest):
    """
    Validates a generated action plan before execution.
    """

    try:
        return action_validator.validate_plan(
            plan=request.plan,
            context=request.context,
            user_approved=request.user_approved,
        )

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )


# ==================================================
# 8. MODULE E — ACTION DISPATCH
# ==================================================

@app.post("/actions/dispatch")
def dispatch_actions(request: DispatchRequest):
    """
    Revalidates the plan and queues actions
    that are approved and ready for execution.
    """

    validation = action_validator.validate_plan(
        plan=request.plan,
        context=request.context,
        user_approved=request.user_approved,
    )

    if not validation.get("valid", False):
        raise HTTPException(
            status_code=422,
            detail="Action plan failed validation.",
        )

    if not validation.get("execution_ready", False):
        raise HTTPException(
            status_code=403,
            detail=(
                "Action plan is not ready for execution "
                "or requires approval."
            ),
        )

    job = execution_manager.submit(
        tab_id=request.tab_id,
        validated=validation,
    )

    return {
        "status": "queued",
        "job": job,
    }


# ==================================================
# 9. MODULE E — GET NEXT ACTION
# ==================================================

@app.get("/actions/next")
def get_next_action(tab_id: int):
    """
    Called by the browser extension to retrieve
    the next pending action for a particular tab.
    """

    action = execution_manager.claim_next(tab_id)

    return {
        "action": action,
    }


# ==================================================
# 10. MODULE E — RECEIVE EXECUTION RESULT
# ==================================================

@app.post("/actions/result")
def receive_execution_result(
    request: ExecutionResultRequest,
):
    """
    Receives execution results from the extension.

    An action is successful only when its result
    has been verified.
    """

    try:
        result = execution_manager.record_result(
            action_id=request.action_id,
            tab_id=request.tab_id,
            result={
                "status": request.status,
                "verified": request.verified,
                "result": request.result,
                "error": request.error,
            },
        )

        return {
            "status": "received",
            "result": result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ==================================================
# 11. MODULE E — JOB STATUS
# ==================================================

@app.get("/actions/jobs/{job_id}")
def get_execution_job(job_id: str):
    """
    Returns the current status of an execution job.
    """

    try:
        job = execution_manager.get_job(job_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Execution job not found.",
        )

    return job


# ==================================================
# 12. MODULE F — VOICE PROCESSING & ACTION DISPATCH
# ==================================================

@app.post("/voice/command")
def process_voice_command(payload: dict):
    """
    Receives voice transcripts from the browser extension, web UI, or microphone,
    routes through Member 3 resolver & matcher, and automatically queues the action
    for the active KiCanvas tab.
    """
    transcript = payload.get("text") or payload.get("transcript")
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Voice text/transcript is required."
        )

    tab_id = payload.get("tab_id")
    profile = payload.get("profile", "PCB_WEB")
    site_type = payload.get("site_type", "KICAD_SCHEMATIC")
    auto_dispatch = payload.get("auto_dispatch", True)

    result = voice_service.process_command(
        transcript=transcript,
        tab_id=tab_id,
        profile=profile,
        site_type=site_type,
        auto_dispatch=auto_dispatch
    )

    return result


@app.get("/voice/status")
def get_voice_status():
    """Returns current Member 3 voice pipeline health, noise, and ASR status."""
    return voice_service.get_status()


# ==================================================
# 13. MODULE G — COMPUTER VISION & WEBSOCKET
# ==================================================

@app.websocket("/ws/cv")
async def cv_websocket_endpoint(websocket: WebSocket):
    """WebSocket stream emitting head gesture and hand tracking events."""
    await cv_service.handle_websocket(websocket)


@app.get("/cv/status")
def get_cv_status():
    """Returns current computer vision, head tracking, and gesture state."""
    return cv_service.get_status()


@app.post("/cv/calibrate")
def calibrate_head_neutral():
    """Calibrates neutral pose for head gesture recognition."""
    success = cv_service.calibrate_neutral()
    return {
        "status": "success" if success else "failed",
        "calibrated": success
    }


@app.post("/cv/reset")
def reset_head_neutral():
    """Resets head gesture calibration."""
    cv_service.reset_neutral()
    return {"status": "success", "calibrated": False}


@app.post("/cv/inject-event")
def inject_cv_event(payload: dict):
    """
    Allows injecting synthetic head or hand events over WebSocket.
    Ideal for automated testing and laboratory workstations without webcams.
    """
    source = payload.get("source", "HEAD")
    action = payload.get("action", "HEAD_UP")
    parameters = payload.get("parameters", {})

    event = cv_service.inject_event(source, action, parameters)
    return {
        "status": "success",
        "injected": event
    }


@app.post("/cv/camera/start")
def start_cv_camera():
    cv_service.start_camera()
    return {"status": "started", "camera_running": cv_service.camera_running}


@app.post("/cv/camera/stop")
def stop_cv_camera():
    cv_service.stop_camera()
    return {"status": "stopped", "camera_running": False}


# ==================================================
# 14. APPLICATION ENTRYPOINT
# ==================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)

