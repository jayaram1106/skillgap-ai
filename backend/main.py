"""
SkillGap AI - FastAPI Backend Application.

Provides endpoints for health verification and AI/heuristic resume-versus-job-description
gap analysis using PyMuPDF and whole-word regex skill matching.
"""

import os
import sys
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

# ---------------------------------------------------------------------------
# FastAPI App Initialization (Preserved from existing setup)
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SkillGap AI API",
    description="Resume vs Job Description Gap Analyser",
    version="1.0.0"
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
# Response Models for Swagger UI Documentation (/docs)
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
# POST /api/analyze Endpoint
# ---------------------------------------------------------------------------

@app.post(
    "/api/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze Resume vs Job Description Gap",
    description=(
        "Upload a PDF resume and job description text to extract skills, compute transparent "
        "compatibility score, identify missing skills, and provide context snippets."
    ),
)
async def analyze_resume_vs_job(
    resume: UploadFile = File(..., description="Candidate PDF resume (Max 5 MB, max 10 pages)"),
    job_description: str = Form(..., description="Target job description text"),
):
    """
    Analyzes an uploaded PDF resume against a job description.

    1. Validates PDF format, signature, size limit (5 MB), and page count (max 10).
    2. Extracts plain text with PyMuPDF (fitz) without logging candidate PII.
    3. Normalizes technical skills to canonical names via a curated dictionary.
    4. Computes matched, missing, and additional skills with context snippets.
    5. Calculates transparent match score: (matched / required) * 100.
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

    # 3. Read file stream safely up to 5 MB + small buffer to detect overflow
    try:
        # Read in chunks to avoid unbounded memory spikes
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
        return result
    except JobDescriptionValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Do not expose internal error or log PII
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing the documents. Please try again.",
        ) from e
