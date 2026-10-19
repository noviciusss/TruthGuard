"""FastAPI surface for the TruthGuard question-answering pipeline."""

from __future__ import annotations

from datetime import date
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import TruthGuardPipeline, build_default_pipeline
from .schemas import FinalAnswer


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    as_of_date: date | None = None


class HealthResponse(BaseModel):
    status: str
    offline: bool


@lru_cache(maxsize=1)
def _default_pipeline() -> TruthGuardPipeline:
    return build_default_pipeline()


def create_app(pipeline: TruthGuardPipeline | None = None) -> FastAPI:
    app = FastAPI(title="TruthGuard API", version="0.1.0")

    def current_pipeline() -> TruthGuardPipeline:
        return pipeline or _default_pipeline()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        offline = bool(current_pipeline().retriever.router.config.get("project", {}).get("offline", True))
        return HealthResponse(status="ok", offline=offline)

    @app.post("/query", response_model=FinalAnswer)
    def query(request: QueryRequest) -> FinalAnswer:
        try:
            return current_pipeline().run(request.question, as_of=request.as_of_date)
        except Exception as exc:  # noqa: BLE001 - expose a clean API error boundary
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
