"""
SkillGap AI - Database Repository Layer.

Handles all CRUD operations with:
- Strict UUID validation.
- Parameterized SQL queries.
- JSON serialization/deserialization for list/dict structures.
- Strict exclusion of raw PDF binary, raw resume text, or sensitive snippets from persistence.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from .database import get_db


def is_valid_uuid(val: Any) -> bool:
    """Validate whether input is a valid RFC 4122 UUID string."""
    if not val or not isinstance(val, str):
        return False
    try:
        uuid_obj = uuid.UUID(val)
        return str(uuid_obj) == val
    except (ValueError, AttributeError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Analysis Sessions CRUD
# ---------------------------------------------------------------------------

def create_analysis_session(
    match_percentage: float,
    summary: str,
    required_skills: List[str],
    resume_skills: List[str],
    matched_skills: List[str],
    missing_skills: List[str],
    additional_skills: List[str],
    score_explanation: str,
    job_description_snippet: str = "",
    job_title: Optional[str] = None,
    session_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    """
    Persist an analysis session into SQLite.

    Security & Privacy rule:
    Only skill metadata, categories, scores, and summary are stored.
    Raw PDF binary, raw resume text, and candidate contact snippets are NEVER stored.
    """
    new_id = session_id or str(uuid.uuid4())
    if not is_valid_uuid(new_id):
        raise ValueError(f"Invalid UUID provided for session_id: {new_id}")

    # Truncate job description snippet to first 300 chars for identification
    clean_snippet = (job_description_snippet or "").strip()[:300]
    if len(job_description_snippet or "") > 300:
        clean_snippet += "..."

    query = """
        INSERT INTO analysis_sessions (
            id,
            job_title,
            job_description_snippet,
            match_percentage,
            summary,
            required_skills,
            resume_skills,
            matched_skills,
            missing_skills,
            additional_skills,
            score_explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        new_id,
        job_title,
        clean_snippet,
        float(match_percentage),
        summary,
        json.dumps(required_skills),
        json.dumps(resume_skills),
        json.dumps(matched_skills),
        json.dumps(missing_skills),
        json.dumps(additional_skills),
        score_explanation,
    )

    with get_db(db_path) as conn:
        conn.execute(query, params)

    return new_id


def get_analysis_session(
    session_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve an analysis session by UUID.
    Returns None if UUID is invalid or record does not exist.
    """
    if not is_valid_uuid(session_id):
        return None

    query = """
        SELECT
            id,
            created_at,
            job_title,
            job_description_snippet,
            match_percentage,
            summary,
            required_skills,
            resume_skills,
            matched_skills,
            missing_skills,
            additional_skills,
            score_explanation
        FROM analysis_sessions
        WHERE id = ?
    """

    with get_db(db_path) as conn:
        cursor = conn.execute(query, (session_id,))
        row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "job_title": row["job_title"],
        "job_description_snippet": row["job_description_snippet"],
        "match_percentage": row["match_percentage"],
        "summary": row["summary"],
        "required_skills": json.loads(row["required_skills"]),
        "resume_skills": json.loads(row["resume_skills"]),
        "matched_skills": json.loads(row["matched_skills"]),
        "missing_skills": json.loads(row["missing_skills"]),
        "additional_skills": json.loads(row["additional_skills"]),
        "score_explanation": row["score_explanation"],
    }


def list_analysis_sessions(
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List recent analysis sessions sorted by newest first."""
    query = """
        SELECT
            id,
            created_at,
            job_title,
            job_description_snippet,
            match_percentage,
            summary,
            required_skills,
            resume_skills,
            matched_skills,
            missing_skills,
            additional_skills,
            score_explanation
        FROM analysis_sessions
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """

    with get_db(db_path) as conn:
        cursor = conn.execute(query, (limit, offset))
        rows = cursor.fetchall()

    sessions = []
    for row in rows:
        sessions.append({
            "id": row["id"],
            "created_at": row["created_at"],
            "job_title": row["job_title"],
            "job_description_snippet": row["job_description_snippet"],
            "match_percentage": row["match_percentage"],
            "summary": row["summary"],
            "required_skills": json.loads(row["required_skills"]),
            "resume_skills": json.loads(row["resume_skills"]),
            "matched_skills": json.loads(row["matched_skills"]),
            "missing_skills": json.loads(row["missing_skills"]),
            "additional_skills": json.loads(row["additional_skills"]),
            "score_explanation": row["score_explanation"],
        })
    return sessions


# ---------------------------------------------------------------------------
# User Preferences CRUD (Session-based with future user_id hook)
# ---------------------------------------------------------------------------

def save_user_preferences(
    session_id: str,
    weekly_hours: int = 10,
    skill_level: str = "intermediate",
    learning_style: str = "hands_on",
    target_timeline_weeks: Optional[int] = None,
    user_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save or update user learning preferences for an analysis session.
    Optional user_id allows linking to future user accounts.
    Optional target_timeline_weeks preserves dynamic completion estimation.
    """
    if not is_valid_uuid(session_id):
        raise ValueError(f"Invalid UUID for session_id: {session_id}")

    if user_id and not is_valid_uuid(user_id):
        raise ValueError(f"Invalid UUID for user_id: {user_id}")

    pref_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    query = """
        INSERT INTO user_preferences (
            id,
            session_id,
            user_id,
            weekly_hours,
            skill_level,
            learning_style,
            target_timeline_weeks,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            user_id = excluded.user_id,
            weekly_hours = excluded.weekly_hours,
            skill_level = excluded.skill_level,
            learning_style = excluded.learning_style,
            target_timeline_weeks = excluded.target_timeline_weeks,
            updated_at = excluded.updated_at
    """

    params = (
        pref_id,
        session_id,
        user_id,
        weekly_hours,
        skill_level,
        learning_style,
        target_timeline_weeks,
        now,
        now,
    )

    with get_db(db_path) as conn:
        conn.execute(query, params)

    return get_user_preferences(session_id, db_path=db_path) or {}


def get_user_preferences(
    session_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve user learning preferences for an analysis session."""
    if not is_valid_uuid(session_id):
        return None

    query = """
        SELECT
            id,
            session_id,
            user_id,
            weekly_hours,
            skill_level,
            learning_style,
            target_timeline_weeks,
            created_at,
            updated_at
        FROM user_preferences
        WHERE session_id = ?
    """

    with get_db(db_path) as conn:
        cursor = conn.execute(query, (session_id,))
        row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "user_id": row["user_id"],
        "weekly_hours": row["weekly_hours"],
        "skill_level": row["skill_level"],
        "learning_style": row["learning_style"],
        "target_timeline_weeks": row["target_timeline_weeks"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
