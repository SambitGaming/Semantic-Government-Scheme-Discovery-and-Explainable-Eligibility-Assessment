"""FastAPI routes for monitored scheme data."""

import os
from fastapi import APIRouter, HTTPException, Query

# Direct relative import within src/automation
from src.automation.myscheme_monitor import (
    get_monitored_scheme,
    list_monitored_schemes,
    list_changes,
    run_monitor,
)

router = APIRouter(
    prefix="/api/monitor",
    tags=["Scheme Monitoring"],
)

DB_PATH = os.getenv(
    "SCHEME_DB_PATH",
    "data/government_schemes.db",
)


@router.get("/schemes")
def get_schemes():
    """List all schemes that have been checked and stored."""
    return {
        "items": list_monitored_schemes(DB_PATH)
    }


@router.get("/schemes/{scheme_id}")
def get_scheme(scheme_id: str):
    """Get the latest monitored snapshot for one scheme."""
    item = get_monitored_scheme(DB_PATH, scheme_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="No monitored snapshot exists for this scheme yet.",
        )

    return item


@router.get("/changes")
def get_scheme_changes(
    scheme_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    """Get detected changes, optionally filtered by scheme ID."""
    return {
        "items": list_changes(DB_PATH, scheme_id, limit)
    }


@router.post("/run")
def run_monitoring(
    scheme_id: list[str] | None = Query(default=None),
):
    """Start a monitoring pass. Restrict this endpoint before deployment."""
    return run_monitor(DB_PATH, scheme_id)