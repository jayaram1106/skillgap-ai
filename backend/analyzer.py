"""
SkillGap AI - Resume and Job Description Analyzer Engine.

Handles:
1. PDF validation (signature, size limits, page limits, encryption, corruption).
2. Robust text extraction using PyMuPDF (fitz).
3. Skill extraction using curated regex patterns with whole-word matching.
4. Contextual evidence extraction for matched, missing, and additional skills.
5. Compatibility score calculation based on required skill coverage.
"""

from typing import Dict, List, Tuple, Any, Optional
import io
import re

try:
    import pymupdf as fitz
except ImportError:
    import fitz

from skills_data import get_skill_definitions


# Constants for PDF validation
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PAGE_LIMIT = 10  # Sensible limit for resumes (typical resume is 1-4 pages)
PDF_MAGIC_SIGNATURE = b"%PDF-"


class PDFValidationError(Exception):
    """Raised when PDF file validation fails."""
    pass


class JobDescriptionValidationError(Exception):
    """Raised when job description text is invalid or lacks detectable skills."""
    pass


def extract_snippet(text: str, match_start: int, match_end: int, window: int = 70) -> str:
    """
    Extract a concise, readable context snippet around a detected skill.
    Identifies natural sentence or line boundaries without clipping words.
    """
    # Look back for line break or sentence start
    start = max(0, match_start - window)
    for i in range(match_start - 1, start - 1, -1):
        if text[i] in "\r\n•\t":
            start = i + 1
            break
        elif i > 1 and text[i - 1 : i + 1] in [". ", "! ", "? "]:
            start = i + 1
            break
    else:
        space = text.find(" ", start, match_start)
        if space != -1:
            start = space + 1

    # Look forward for line break or sentence end
    end = min(len(text), match_end + window)
    for i in range(match_end, end):
        if text[i] in "\r\n•\t":
            end = i
            break
        elif i + 1 < len(text) and text[i : i + 2] in [". ", "! ", "? "]:
            end = i + 1
            break
    else:
        space = text.rfind(" ", match_end, end)
        if space != -1:
            end = space

    snippet = " ".join(text[start:end].split()).strip()
    snippet = re.sub(r"^[•\-\*\>\s]+", "", snippet)

    prefix = "... " if start > 0 and not snippet.startswith("...") else ""
    suffix = " ..." if end < len(text) and not snippet.endswith("...") else ""
    result = f"{prefix}{snippet}{suffix}".strip()
    return result if result else text[match_start:match_end]


def validate_and_extract_pdf_text(pdf_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Validate uploaded PDF file integrity, size, signature, and extract readable text.

    Raises:
        PDFValidationError: If the file is invalid, corrupt, oversized, or unreadable.
    """
    # 1. Check non-empty
    if not pdf_bytes or len(pdf_bytes) == 0:
        raise PDFValidationError("The uploaded file is empty (0 bytes). Please upload a valid PDF resume.")

    # 2. Check 5 MB upload limit
    if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = round(len(pdf_bytes) / (1024 * 1024), 2)
        raise PDFValidationError(
            f"File size exceeds the 5 MB limit. Uploaded file is {size_mb} MB."
        )

    # 3. Check PDF magic signature (%PDF-)
    # Per ISO 32000-1, %PDF- must appear in the header (typically within the first 1024 bytes)
    header_chunk = pdf_bytes[:1024]
    if PDF_MAGIC_SIGNATURE not in header_chunk:
        raise PDFValidationError(
            "Invalid PDF signature. The uploaded file is not a valid PDF document."
        )

    # 4. Open document with PyMuPDF
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise PDFValidationError(
            "Failed to parse PDF document. The file may be corrupt or not formatted properly."
        ) from e

    try:
        # 5. Check encryption / password protection
        if doc.is_encrypted or doc.needs_pass:
            raise PDFValidationError(
                "Password-protected PDFs are not supported. Please upload an unprotected PDF."
            )

        # 6. Check sensible page limit
        page_count = doc.page_count
        if page_count == 0:
            raise PDFValidationError("The uploaded PDF document contains no pages.")
        if page_count > MAX_PAGE_LIMIT:
            raise PDFValidationError(
                f"PDF exceeds the maximum allowed limit of {MAX_PAGE_LIMIT} pages for a resume. "
                f"The document contains {page_count} pages."
            )

        # 7. Extract text from pages
        text_parts = []
        for page_idx in range(page_count):
            page = doc.load_page(page_idx)
            page_text = page.get_text()
            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

        extracted_text = "\n\n".join(text_parts).strip()
        if not extracted_text:
            raise PDFValidationError(
                "No readable text found in the PDF. Please ensure the resume is text-based and not a scanned image."
            )

        return extracted_text

    finally:
        # Guarantee document closure to free resources
        doc.close()


def extract_skills_from_text(text: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract skills from text using curated regex patterns and whole-word matching.
    Returns a mapping:
        canonical_name -> {
            "canonical": canonical_name,
            "category": category,
            "evidence": snippet_str
        }
    """
    if not text:
        return {}

    detected_skills: Dict[str, Dict[str, Any]] = {}
    definitions = get_skill_definitions()

    for item in definitions:
        canonical = item["canonical"]
        category = item["category"]
        pattern = item["pattern"]

        match = pattern.search(text)
        if match:
            # Capture contextual evidence snippet around the match
            snippet = extract_snippet(text, match.start(), match.end())
            detected_skills[canonical] = {
                "canonical": canonical,
                "category": category,
                "evidence": snippet,
            }

    return detected_skills


def analyze_gap(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Analyze skill gap between resume text and job description.

    Calculates:
        - matched_skills: Skills present in both resume and job description.
        - missing_skills: Skills required by job description but missing from resume.
        - additional_skills: Skills on resume that were not requested in job description.
        - match_percentage: (matched_required / total_required) * 100.
        - evidence: Contextual text snippets showing where each skill was identified.

    Raises:
        JobDescriptionValidationError: If job description is empty or has no recognizable skills.
    """
    cleaned_jd = job_description.strip() if job_description else ""
    if not cleaned_jd:
        raise JobDescriptionValidationError("Job description cannot be empty. Please provide job description text.")

    if len(cleaned_jd) < 20:
        raise JobDescriptionValidationError(
            "Job description is too brief. Please provide a more detailed job description."
        )

    # Extract skills separately
    job_skills_map = extract_skills_from_text(cleaned_jd)
    resume_skills_map = extract_skills_from_text(resume_text)

    # Validate that the job description contains detectable technical skills
    if not job_skills_map:
        raise JobDescriptionValidationError(
            "No recognizable technical skills were detected in the provided job description. "
            "Please provide a job description containing specific technologies, programming languages, "
            "or technical requirements. Note: The compatibility score measures skill coverage, not "
            "the probability of getting hired."
        )

    # Compute skill sets
    required_skills = sorted(list(job_skills_map.keys()))
    resume_skills = sorted(list(resume_skills_map.keys()))

    matched_skills = sorted([s for s in required_skills if s in resume_skills_map])
    missing_skills = sorted([s for s in required_skills if s not in resume_skills_map])
    additional_skills = sorted([s for s in resume_skills if s not in job_skills_map])

    # Calculate transparent compatibility score
    # Score = (matched required skills / total required skills) * 100
    total_required = len(required_skills)
    total_matched = len(matched_skills)
    match_percentage = round((total_matched / total_required) * 100, 2)

    # Assemble structured evidence snippets
    evidence_matched = []
    for skill in matched_skills:
        evidence_matched.append({
            "skill": skill,
            "category": job_skills_map[skill]["category"],
            "resume_evidence": resume_skills_map[skill]["evidence"],
            "job_evidence": job_skills_map[skill]["evidence"],
            "resume_snippet": resume_skills_map[skill]["evidence"],
            "job_snippet": job_skills_map[skill]["evidence"],
        })

    evidence_missing = []
    for skill in missing_skills:
        evidence_missing.append({
            "skill": skill,
            "category": job_skills_map[skill]["category"],
            "job_evidence": job_skills_map[skill]["evidence"],
            "job_snippet": job_skills_map[skill]["evidence"],
            "resume_evidence": None,
            "resume_snippet": None,
        })

    evidence_additional = []
    for skill in additional_skills:
        evidence_additional.append({
            "skill": skill,
            "category": resume_skills_map[skill]["category"],
            "resume_evidence": resume_skills_map[skill]["evidence"],
            "resume_snippet": resume_skills_map[skill]["evidence"],
            "job_evidence": None,
            "job_snippet": None,
        })

    # Generate a clear, professional summary
    score_note = (
        "Note: This compatibility score measures technical skill coverage against specified job "
        "requirements, not the overall probability of getting hired."
    )

    if match_percentage >= 80.0:
        alignment_level = "Strong"
    elif match_percentage >= 50.0:
        alignment_level = "Moderate"
    else:
        alignment_level = "Low"

    summary_parts = [
        f"{alignment_level} skill alignment ({match_percentage}%).",
        f"Matched {total_matched} of {total_required} required skills ({', '.join(matched_skills) if matched_skills else 'None'}).",
    ]
    if missing_skills:
        summary_parts.append(f"Missing required skills: {', '.join(missing_skills)}.")
    if additional_skills:
        summary_parts.append(f"Additional candidate skills identified: {', '.join(additional_skills)}.")
    summary_parts.append(score_note)

    summary = " ".join(summary_parts)

    return {
        "success": True,
        "match_percentage": match_percentage,
        "summary": summary,
        "required_skills": required_skills,
        "resume_skills": resume_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "additional_skills": additional_skills,
        "resume_only_skills": additional_skills,
        "evidence": {
            "matched_skills": evidence_matched,
            "missing_skills": evidence_missing,
            "additional_skills": evidence_additional,
        },
        "score_explanation": (
            f"Compatibility score ({match_percentage}%) is calculated as (matched_skills / required_skills) * 100 "
            f"({total_matched} / {total_required} * 100). It measures technical skill coverage, not hiring probability."
        ),
    }
