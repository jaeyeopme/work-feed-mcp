"""Compatibility shim for collector-record validation."""

from upwork_app.domain.collector_record import (
    CollectorRecord,
    canonical_payload_json,
    content_hash_for_payload_json,
    validate_payload,
)

__all__ = [
    "CollectorRecord",
    "canonical_payload_json",
    "content_hash_for_payload_json",
    "validate_payload",
]
