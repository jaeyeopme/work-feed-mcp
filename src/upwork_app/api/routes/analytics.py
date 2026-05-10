from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from upwork_app.api.deps import settings
from upwork_app.core.config import Settings
from upwork_app.schemas.analytics import AnalyticsResponse
from upwork_app.services.analytics import AnalyticsServiceError, query_database

settings_dependency = Depends(settings)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{name}", response_model=AnalyticsResponse)
def analytics_query(
    name: str,
    skill: str | None = None,
    title: str | None = None,
    app_settings: Settings = settings_dependency,
) -> AnalyticsResponse:
    if name not in {"summary", "skills", "jobs", "budgets", "runs", "clients"}:
        raise HTTPException(status_code=404, detail="unknown analytics query")
    try:
        result = query_database(app_settings.default_db_path, name, skill=skill, title=title)
    except AnalyticsServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return AnalyticsResponse(**result.to_dict())
