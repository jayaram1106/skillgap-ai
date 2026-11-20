"""
SkillGap AI - FastAPI Backend Application.

Provides endpoints for health verification, AI/heuristic resume-versus-job-description
gap analysis using PyMuPDF, whole-word regex skill matching, and SQLite persistence.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure current module directory is on sys.path for direct uvicorn launches
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from analyzer import (
    validate_and_extract_pdf_text,
    analyze_gap,
    PDFValidationError,
    JobDescriptionValidationError,
    MAX_FILE_SIZE_BYTES,
)

from db import (
    init_db,
    create_analysis_session,
    get_analysis_session,
    list_analysis_sessions,
    save_user_preferences,
    get_user_preferences,
    is_valid_uuid,
)


# ---------------------------------------------------------------------------
# FastAPI App Lifecycle & Initialization
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and WAL mode on application startup."""
    init_db()
    yield


app = FastAPI(
    title="SkillGap AI API",
    description="Resume vs Job Description Gap Analyser",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React frontend to communicate with backend
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Response & Request Models for Swagger UI Documentation (/docs)
# ---------------------------------------------------------------------------

class SkillEvidenceItem(BaseModel):
    skill: str = Field(..., description="Canonical name of the detected skill")
    category: str = Field(..., description="Technical domain category of the skill")
    resume_evidence: Optional[str] = Field(None, description="Contextual snippet from the resume")
    job_evidence: Optional[str] = Field(None, description="Contextual snippet from the job description")
    resume_snippet: Optional[str] = Field(None, description="Alias for resume_evidence")
    job_snippet: Optional[str] = Field(None, description="Alias for job_evidence")


class EvidenceReport(BaseModel):
    matched_skills: List[SkillEvidenceItem] = Field(
        default_factory=list,
        description="Skills present in both resume and job description with evidence"
    )
    missing_skills: List[SkillEvidenceItem] = Field(
        default_factory=list,
        description="Skills required by job description but missing from resume"
    )
    additional_skills: List[SkillEvidenceItem] = Field(
        default_factory=list,
        description="Skills found on resume but not required by job description"
    )


class AnalyzeResponse(BaseModel):
    success: bool = Field(True, description="Whether the analysis succeeded")
    session_id: str = Field(..., description="Unique database UUID for this analysis session")
    match_percentage: float = Field(..., description="Compatibility score ((matched / required) * 100)")
    summary: str = Field(..., description="Human-readable assessment and alignment overview")
    required_skills: List[str] = Field(..., description="All technical skills detected in the job description")
    resume_skills: List[str] = Field(..., description="All technical skills detected in the resume")
    matched_skills: List[str] = Field(..., description="Skills present in both resume and job description")
    missing_skills: List[str] = Field(..., description="Required skills not found on candidate resume")
    additional_skills: List[str] = Field(..., description="Candidate skills not specified in job description")
    resume_only_skills: List[str] = Field(..., description="Alias for additional_skills")
    evidence: EvidenceReport = Field(..., description="Contextual text snippets for detected and missing skills")
    score_explanation: str = Field(..., description="Detailed explanation of how the score is calculated")


class PreferencesRequest(BaseModel):
    weekly_hours: int = Field(10, ge=1, le=168, description="Target study hours per week")
    skill_level: str = Field("intermediate", description="beginner | intermediate | advanced")
    learning_style: str = Field("hands_on", description="hands_on | video_first | reading_docs | project_based")
    target_timeline_weeks: Optional[int] = Field(None, ge=1, description="Optional target weeks")
    user_id: Optional[str] = Field(None, description="Optional user account UUID")


# ---------------------------------------------------------------------------
# Existing Health & Root Endpoints (Preserved)
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to SkillGap AI",
        "status": "Backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "SkillGap AI",
        "backend": "FastAPI"
    }


# ---------------------------------------------------------------------------
# POST /api/analyze Endpoint (Preserved & Enhanced with Session Persistence)
# ---------------------------------------------------------------------------

@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Resume vs Job Description Gap",
    description=(
        "Upload a PDF resume and job description text to extract skills, compute transparent "
        "compatibility score, identify missing skills, provide context snippets, and persist session."
    ),
)
async def analyze_resume_vs_job(
    resume: UploadFile = File(..., description="Candidate PDF resume (Max 5 MB, max 10 pages)"),
    job_description: str = Form(..., description="Target job description text"),
):
    """
    Analyzes an uploaded PDF resume against a job description.

    1. Validates PDF format, signature, size limit (5 MB), and page count (max 10).
    2. Extracts plain text with PyMuPDF (fitz) in-memory without logging candidate PII.
    3. Normalizes technical skills to canonical names via a curated dictionary.
    4. Computes matched, missing, and additional skills with context snippets.
    5. Calculates transparent match score: (matched / required) * 100.
    6. Persists session metadata, score, and skill names in SQLite (without storing PDF or resume text).
    """
    # 1. Validate file extension
    filename = resume.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension for '{filename}'. Only PDF documents (.pdf) are accepted.",
        )

    # 2. Validate MIME content-type header if supplied
    if resume.content_type and not (
        "pdf" in resume.content_type.lower()
        or resume.content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{resume.content_type}'. Expected 'application/pdf'.",
        )

    # 3. Read file stream safely up to 5 MB
    try:
        pdf_bytes = bytearray()
        chunk_size = 1024 * 1024  # 1 MB chunk
        while True:
            chunk = await resume.read(chunk_size)
            if not chunk:
                break
            pdf_bytes.extend(chunk)
            if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds the 5 MB limit. Please upload a smaller PDF resume.",
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading uploaded file stream.",
        ) from e
    finally:
        await resume.close()

    # 4. Validate PDF integrity, signature, page limits, and extract text via PyMuPDF
    try:
        resume_text = validate_and_extract_pdf_text(bytes(pdf_bytes), filename)
    except PDFValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 5. Perform skill gap analysis
    try:
        result = analyze_gap(resume_text, job_description)
    except JobDescriptionValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the documents. Please try again.",
        ) from e

    # 6. Persist analysis session to SQLite (Strict privacy: NO raw resume text or PDFs stored)
    try:
        session_id = create_analysis_session(
            match_percentage=result["match_percentage"],
            summary=result["summary"],
            required_skills=result["required_skills"],
            resume_skills=result["resume_skills"],
            matched_skills=result["matched_skills"],
            missing_skills=result["missing_skills"],
            additional_skills=result["additional_skills"],
            score_explanation=result["score_explanation"],
            job_description_snippet=job_description,
        )
        result["session_id"] = session_id
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis succeeded but failed to persist session record.",
        ) from e


# ---------------------------------------------------------------------------
# Sessions & Preferences Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/api/sessions/{session_id}",
    summary="Retrieve Analysis Session",
    description="Retrieve a previously saved analysis session by its UUID."
)
def get_session_by_id(session_id: str):
    """Retrieve saved analysis session and any optional user preferences."""
    if not is_valid_uuid(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session UUID format: '{session_id}'."
        )

    session = get_analysis_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{session_id}' was not found."
        )

    preferences = get_user_preferences(session_id)
    return {
        "success": True,
        "session": session,
        "preferences": preferences,
    }


@app.get(
    "/api/sessions",
    summary="List Recent Analysis Sessions",
    description="List recent analysis sessions sorted by newest first."
)
def list_sessions(limit: int = 20, offset: int = 0):
    """List recent analysis sessions."""
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100."
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative."
        )

    sessions = list_analysis_sessions(limit=limit, offset=offset)
    return {
        "success": True,
        "count": len(sessions),
        "sessions": sessions,
    }


@app.post(
    "/api/sessions/{session_id}/preferences",
    summary="Save User Learning Preferences",
    description="Save or update learning preferences for an analysis session."
)
def update_preferences(session_id: str, payload: PreferencesRequest):
    """Save or update user learning preferences for an analysis session."""
    if not is_valid_uuid(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session UUID format: '{session_id}'."
        )

    # Verify session exists
    session = get_analysis_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{session_id}' was not found."
        )

    valid_levels = {"beginner", "intermediate", "advanced"}
    if payload.skill_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid skill_level '{payload.skill_level}'. Choose from {sorted(list(valid_levels))}."
        )

    valid_styles = {"hands_on", "video_first", "reading_docs", "project_based"}
    if payload.learning_style not in valid_styles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid learning_style '{payload.learning_style}'. Choose from {sorted(list(valid_styles))}."
        )

    prefs = save_user_preferences(
        session_id=session_id,
        weekly_hours=payload.weekly_hours,
        skill_level=payload.skill_level,
        learning_style=payload.learning_style,
        target_timeline_weeks=payload.target_timeline_weeks,
        user_id=payload.user_id,
    )

    return {
        "success": True,
        "session_id": session_id,
        "preferences": prefs,
    }


@app.get(
    "/api/sessions/{session_id}/preferences",
    summary="Get User Learning Preferences",
    description="Get user learning preferences for an analysis session."
)
def retrieve_preferences(session_id: str):
    """Retrieve learning preferences for an analysis session."""
    if not is_valid_uuid(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session UUID format: '{session_id}'."
        )

    session = get_analysis_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{session_id}' was not found."
        )

    prefs = get_user_preferences(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "preferences": prefs,
    }
