"""FastAPI application for the Government Scheme Assistant."""

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from src.app.retrieval_service import semantic_search
from src.app.services import (
    evaluate_scheme_eligibility,
    get_scheme_details,
    get_schemes,
)
from src.app.auth_service import (
    create_session,
    get_connection,
    get_current_user,
    get_profile,
    hash_password,
    revoke_session,
    save_profile,
    verify_password,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = FastAPI(
    title="Government Scheme Assistant API",
    version="1.1.0",
    description=(
        "Semantic government scheme discovery, user authentication, "
        "personalized scholarship recommendations, and explainable "
        "eligibility assessment API"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class UserProfile(BaseModel):
    """Profile fields used by eligibility assessment and saved profiles."""

    # Accept dynamic eligibility fields generated from scheme rules.
    # Without this setting, Pydantic rejects undeclared fields.
    model_config = ConfigDict(extra="allow")

    age: Optional[int] = Field(default=None, ge=1, le=120)
    gender: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    annual_income: Optional[float] = Field(default=None, ge=0)
    education_level: Optional[str] = None
    study_mode: Optional[str] = None
    course: Optional[str] = None
    occupation: Optional[str] = None
    year_of_study: Optional[int] = Field(default=None, ge=1, le=15)
    disability_percentage: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    # Additional fields such as these are accepted automatically:
    # receives_other_scholarship
    # is_government_employee
    # family_income
    # institution_type
    # marital_status


class RegisterRequest(BaseModel):
    """New account registration details."""

    username: str = Field(min_length=3, max_length=30)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Username/email and password for login."""

    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


# ============================================================
# HELPERS
# ============================================================

def get_scheme_id(scheme: dict):
    """Read a scheme identifier across supported data formats."""

    return (
        scheme.get("scheme_id")
        or scheme.get("id")
        or scheme.get("ID")
    )


def normalize_eligibility_result(result):
    """Extract an explicit eligibility decision when available."""

    if isinstance(result, bool):
        return result

    if not isinstance(result, dict):
        return None

    for key in (
        "eligible",
        "is_eligible",
        "isEligible",
        "eligibility",
    ):
        value = result.get(key)

        if isinstance(value, bool):
            return value

    for key in (
        "status",
        "eligibility_status",
        "result",
    ):
        value = result.get(key)

        if not isinstance(value, str):
            continue

        normalized = (
            value.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if normalized in {
            "eligible",
            "qualified",
            "meets_requirements",
        }:
            return True

        if normalized in {
            "ineligible",
            "not_eligible",
            "not_qualified",
            "does_not_qualify",
        }:
            return False

    return None


def get_scheme_display_name(scheme: dict) -> str:
    """Get a readable scheme name from supported data formats."""

    return str(
        scheme.get("scheme_name")
        or scheme.get("Scholarship")
        or scheme.get("name")
        or "Government Scheme"
    )


# ============================================================
# GENERAL API
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to the Government Scheme Assistant API",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Government Scheme Assistant API",
    }


# ============================================================
# SCHEME LISTING AND DETAILS
# ============================================================

@app.get("/schemes")
def list_schemes():
    """Return schemes from the existing data source."""

    try:
        schemes = get_schemes()

        return {
            "count": len(schemes),
            "schemes": schemes,
        }

    except Exception as error:
        logger.exception("Could not retrieve schemes.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve schemes.",
        ) from error


@app.get("/schemes/{scheme_id}")
def scheme_details(scheme_id: str):
    """Return details for one scheme."""

    try:
        scheme = get_scheme_details(scheme_id)

        if not scheme:
            raise HTTPException(
                status_code=404,
                detail=f"Scheme '{scheme_id}' was not found.",
            )

        return scheme

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Could not retrieve scheme details for %s.",
            scheme_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve scheme details.",
        ) from error


# ============================================================
# INDIVIDUAL SCHEME ELIGIBILITY
# ============================================================

@app.post("/schemes/{scheme_id}/eligibility")
def check_scheme_eligibility(
    scheme_id: str,
    profile: UserProfile,
):
    """Evaluate eligibility for a specific scheme."""

    try:
        # Keep dynamically supplied fields and discard only None values.
        profile_data = profile.model_dump(exclude_none=True)

        result = evaluate_scheme_eligibility(
            scheme_id,
            profile_data,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scheme '{scheme_id}' was not found.",
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Eligibility evaluation failed for %s.",
            scheme_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Could not evaluate scheme eligibility.",
        ) from error


# ============================================================
# SEMANTIC SEARCH
# ============================================================

@app.get("/search")
def search_schemes(
    q: str = Query(
        ...,
        min_length=1,
        description="Search for a government scheme",
    ),
    model: str = Query(
        "minilm",
        description="Semantic model: minilm or mpnet",
    ),
    top_k: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of results",
    ),
):
    """Search schemes using semantic retrieval."""

    q = q.strip()
    model = model.strip().lower()

    if not q:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    if model not in {"minilm", "mpnet"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid model. Use 'minilm' or 'mpnet'.",
        )

    try:
        results = semantic_search(
            query=q,
            model=model,
            top_k=top_k,
        )

        return {
            "query": q,
            "model": model,
            "count": len(results),
            "results": results,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Semantic search failed.")

        # Avoid returning internal exception details to API clients.
        raise HTTPException(
            status_code=500,
            detail="Semantic search failed. Check the backend logs.",
        ) from error


# ============================================================
# USER REGISTRATION
# ============================================================

@app.post("/auth/register", status_code=201)
def register_user(request: RegisterRequest):
    """Create an account and start an authenticated session."""

    username = request.username.strip()
    email = request.email.strip().lower()

    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
        raise HTTPException(
            status_code=400,
            detail=(
                "Username must be 3-30 characters and contain only "
                "letters, numbers, dots, underscores or hyphens."
            ),
        )

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid email address.",
        )

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username,
                    email,
                    password_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    hash_password(request.password),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

            user_id = cursor.lastrowid
            connection.commit()

        token = create_session(user_id)

        return {
            "message": "Account created successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "username": username,
                "email": email,
            },
            "profile_completed": False,
        }

    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="That username or email is already registered.",
        ) from error

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("User registration failed.")

        raise HTTPException(
            status_code=500,
            detail="Could not create the account.",
        ) from error


# ============================================================
# USER LOGIN
# ============================================================

@app.post("/auth/login")
def login_user(request: LoginRequest):
    """Authenticate using either username or email."""

    identifier = request.identifier.strip()

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT user_id, username, email, password_hash
            FROM users
            WHERE username = ? COLLATE NOCASE
               OR email = ? COLLATE NOCASE
            """,
            (identifier, identifier),
        ).fetchone()

    if not user or not verify_password(
        request.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password.",
        )

    token = create_session(user["user_id"])
    profile = get_profile(user["user_id"])

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
        },
        "profile_completed": profile is not None,
    }


# ============================================================
# CURRENT USER AND LOGOUT
# ============================================================

@app.get("/auth/me")
def get_logged_in_user(
    user: dict = Depends(get_current_user),
):
    """Return the authenticated user's public account information."""

    return {
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
        },
        "profile_completed": (
            get_profile(user["user_id"]) is not None
        ),
    }


@app.post("/auth/logout")
def logout_user(
    user: dict = Depends(get_current_user),
):
    """Revoke the current session."""

    revoke_session(user["token_hash"])

    return {"message": "Logged out successfully."}


# ============================================================
# SAVED SCHOLARSHIP QUESTIONNAIRE
# ============================================================

@app.get("/auth/profile")
def read_user_profile(
    user: dict = Depends(get_current_user),
):
    """Read the current user's saved questionnaire answers."""

    profile = get_profile(user["user_id"])

    return {
        "profile": profile,
        "profile_completed": profile is not None,
    }


@app.put("/auth/profile")
def update_user_profile(
    profile: UserProfile,
    user: dict = Depends(get_current_user),
):
    """Save or update the current user's questionnaire answers."""

    data = profile.model_dump(exclude_none=True)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one profile answer.",
        )

    try:
        save_profile(user["user_id"], data)

        return {
            "message": "Profile saved successfully.",
            "profile": get_profile(user["user_id"]),
            "profile_completed": True,
        }

    except Exception as error:
        logger.exception("Could not save user profile.")

        raise HTTPException(
            status_code=500,
            detail="Could not save your profile.",
        ) from error


# ============================================================
# AUTOMATIC SCHOLARSHIP RECOMMENDATIONS
# ============================================================

@app.post("/auth/recommendations")
def recommend_scholarships(
    user: dict = Depends(get_current_user),
):
    """Assess the user's saved profile against available schemes."""

    profile = get_profile(user["user_id"])

    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Complete your scholarship questionnaire first.",
        )

    try:
        schemes = get_schemes()

        recommendations = []
        needs_review = []
        evaluation_errors = []

        for scheme in schemes:
            if not isinstance(scheme, dict):
                continue

            scheme_id = get_scheme_id(scheme)

            if scheme_id is None:
                logger.warning(
                    "Skipping scheme without an ID: %s",
                    get_scheme_display_name(scheme),
                )
                continue

            try:
                result = evaluate_scheme_eligibility(
                    str(scheme_id),
                    profile,
                )

                if result is None:
                    continue

                eligible = normalize_eligibility_result(result)

                item = {
                    **scheme,
                    "eligibility_result": result,
                }

                if eligible is True:
                    item["assessment_status"] = "eligible"
                    recommendations.append(item)

                elif eligible is False:
                    continue

                else:
                    item["assessment_status"] = "needs_review"
                    item["assessment_note"] = (
                        "The eligibility service did not return a "
                        "recognized eligible/ineligible status. "
                        "Review the assessment before relying on it."
                    )
                    needs_review.append(item)

            except Exception:
                logger.exception(
                    "Could not assess scheme %s for user %s.",
                    scheme_id,
                    user["user_id"],
                )

                evaluation_errors.append({
                    "scheme_id": str(scheme_id),
                    "scheme_name": get_scheme_display_name(scheme),
                })

        return {
            "profile": profile,
            "count": len(recommendations),
            "recommendations": recommendations,
            "needs_review": needs_review,
            "evaluation_errors": evaluation_errors,
            "message": (
                "Assessment completed. Confirmed matches, uncertain "
                "results and assessment errors are reported separately."
            ),
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Scholarship recommendations failed.")

        raise HTTPException(
            status_code=500,
            detail="Could not generate scholarship recommendations.",
        ) from error


# ============================================================
# DAY 25 AUTOMATION CANDIDATES
# ============================================================

@app.get("/api/automation/candidates")
def get_extracted_candidates():
    """Read extraction candidate JSON files from pending_review."""

    pending_dir = (
        PROJECT_ROOT
        / "data"
        / "automation"
        / "pending_review"
    )

    if not pending_dir.exists():
        return {
            "count": 0,
            "candidates": [],
            "data_source": "day25_extraction_json",
            "message": (
                "The pending_review folder does not exist yet. "
                "Run the extraction bot first."
            ),
        }

    candidates = []

    for file_path in sorted(pending_dir.glob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as file:
                record = json.load(file)

            if not isinstance(record, dict):
                logger.warning(
                    "Skipping %s: JSON content is not an object.",
                    file_path.name,
                )
                continue

            record["review_status"] = "pending_review"
            record["candidate_file"] = file_path.name
            candidates.append(record)

        except (json.JSONDecodeError, OSError):
            logger.exception(
                "Could not read candidate file %s.",
                file_path.name,
            )

    return {
        "count": len(candidates),
        "candidates": candidates,
        "data_source": "day25_extraction_json",
        "review_required": True,
    }


# ============================================================
# SCHEME MONITORING ROUTER
# ============================================================

try:
    from src.automation.monitor_api import router as monitor_router

    app.include_router(monitor_router)

except ImportError:
    logger.warning(
        "Scheme-monitoring router could not be imported. "
        "The main API will continue without it."
    )


@app.get("/monitor-health")
def monitor_health():
    """Describe the scheme-monitoring API endpoints."""

    return {
        "status": "available",
        "endpoints": [
            "/api/monitor/schemes",
            "/api/monitor/schemes/{scheme_id}",
            "/api/monitor/changes",
            "/api/monitor/run",
        ],
    }