from __future__ import annotations

from upwork_app.integrations.upwork.models import Job


def test_job_serialization_is_json_compatible() -> None:
    job = Job(
        source="upwork",
        id="cipher",
        title="Title",
        description="Description",
        url="https://www.upwork.com/jobs/cipher",
        skills=["Python"],
        hourly_min=10.0,
        hourly_max=None,
    )

    data = job.to_dict()

    assert data["skills"] == ["Python"]
    assert isinstance(data["skills"], list)
    assert data["hourly_min"] == 10.0
    assert data["hourly_max"] is None
    assert data["posted_at"] is None
