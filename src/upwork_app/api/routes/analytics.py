from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from upwork_app.api.deps import settings
from upwork_app.core.config import Settings
from upwork_app.schemas.analytics import AnalyticsResponse
from upwork_app.services.analytics import AnalyticsServiceError, query_database

settings_dependency = Depends(settings)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _analytics_response(
    app_settings: Settings,
    name: str,
    *,
    skill: str | None = None,
    title: str | None = None,
) -> AnalyticsResponse:
    try:
        result = query_database(app_settings.default_db_path, name, skill=skill, title=title)
    except AnalyticsServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return AnalyticsResponse(**result.to_dict())


@router.get("/summary", response_model=AnalyticsResponse)
def summary(app_settings: Settings = settings_dependency) -> AnalyticsResponse:
    return _analytics_response(app_settings, "summary")


@router.get("/skills", response_model=AnalyticsResponse)
def skills(app_settings: Settings = settings_dependency) -> AnalyticsResponse:
    return _analytics_response(app_settings, "skills")


@router.get("/jobs", response_model=AnalyticsResponse)
def jobs(
    skill: str | None = None,
    title: str | None = None,
    app_settings: Settings = settings_dependency,
) -> AnalyticsResponse:
    return _analytics_response(app_settings, "jobs", skill=skill, title=title)


@router.get("/budgets", response_model=AnalyticsResponse)
def budgets(app_settings: Settings = settings_dependency) -> AnalyticsResponse:
    return _analytics_response(app_settings, "budgets")


@router.get("/runs", response_model=AnalyticsResponse)
def runs(app_settings: Settings = settings_dependency) -> AnalyticsResponse:
    return _analytics_response(app_settings, "runs")


@router.get("/clients", response_model=AnalyticsResponse)
def clients(app_settings: Settings = settings_dependency) -> AnalyticsResponse:
    return _analytics_response(app_settings, "clients")
