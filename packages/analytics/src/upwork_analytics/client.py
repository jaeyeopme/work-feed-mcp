"""Compatibility shim for client analytics."""

from upwork_app.repositories.client_analytics import (
    DEFAULT_CLIENT_DIMENSIONS,
    ClientDimension,
    ClientDimensionBucket,
    client_dimension_buckets,
)

__all__ = [
    "DEFAULT_CLIENT_DIMENSIONS",
    "ClientDimension",
    "ClientDimensionBucket",
    "client_dimension_buckets",
]
