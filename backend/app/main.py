from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import AdvisoryRequest, AdvisoryResponse
from .coordination.coordinator import AdvisoryCoordinator


app = FastAPI(title="Multi-Agent AI Farm Advisory System", version="0.1.0")

# Allow local dev frontends by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

coordinator = AdvisoryCoordinator()


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/advisory", response_model=AdvisoryResponse)
def get_advisory(payload: AdvisoryRequest):
    try:
        plan = coordinator.build_advisory_plan(payload)
        return plan
    except Exception as exc:  # pragma: no cover - basic safety net
        raise HTTPException(status_code=500, detail=str(exc))


# For `python -m uvicorn backend.app.main:app --reload`
def get_app() -> FastAPI:
    return app


