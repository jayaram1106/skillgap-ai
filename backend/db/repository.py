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


# ---------------------------------------------------------------------------
# Learning Roadmaps & Tasks CRUD
# ---------------------------------------------------------------------------

def create_learning_roadmap(
    session_id: str,
    title: str,
    target_role: Optional[str],
    total_estimated_hours: float,
    roadmap_metadata: Dict[str, Any],
    tasks: List[Dict[str, Any]],
    roadmap_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    """
    Persist a generated learning roadmap and its constituent actionable tasks.
    Deletes any existing roadmap for this session to ensure a single active roadmap.
    """
    if not is_valid_uuid(session_id):
        raise ValueError(f"Invalid UUID for session_id: {session_id}")

    new_roadmap_id = roadmap_id or str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_db(db_path) as conn:
        # Cascade delete prior roadmap for this session
        conn.execute("DELETE FROM learning_roadmaps WHERE session_id = ?", (session_id,))

        insert_roadmap_query = """
            INSERT INTO learning_roadmaps (
                id,
                session_id,
                title,
                target_role,
                total_estimated_hours,
                status,
                roadmap_metadata,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """
        conn.execute(
            insert_roadmap_query,
            (
                new_roadmap_id,
                session_id,
                title,
                target_role,
                float(total_estimated_hours),
                json.dumps(roadmap_metadata),
                now,
                now,
            ),
        )

        insert_task_query = """
            INSERT INTO roadmap_tasks (
                id,
                roadmap_id,
                skill_name,
                skill_category,
                module_order,
                task_title,
                task_description,
                resource_url,
                estimated_minutes,
                is_completed,
                completed_at,
                notes,
                prerequisites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for t in tasks:
            task_id = t.get("id") or str(uuid.uuid4())
            prereqs = t.get("prerequisites")
            prereqs_json = json.dumps(prereqs) if isinstance(prereqs, list) else (prereqs or None)
            conn.execute(
                insert_task_query,
                (
                    task_id,
                    new_roadmap_id,
                    t["skill_name"],
                    t.get("skill_category", "Technical Skill"),
                    int(t.get("module_order", 1)),
                    t["task_title"],
                    t.get("task_description", ""),
                    t.get("resource_url"),
                    int(t.get("estimated_minutes", 60)),
                    1 if t.get("is_completed") else 0,
                    t.get("completed_at"),
                    t.get("notes"),
                    prereqs_json,
                ),
            )

    return new_roadmap_id


def get_learning_roadmap_by_session(
    session_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve the learning roadmap and all tasks for an analysis session."""
    if not is_valid_uuid(session_id):
        return None

    query = """
        SELECT
            id,
            session_id,
            title,
            target_role,
            total_estimated_hours,
            status,
            roadmap_metadata,
            created_at,
            updated_at
        FROM learning_roadmaps
        WHERE session_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """

    with get_db(db_path) as conn:
        cursor = conn.execute(query, (session_id,))
        roadmap_row = cursor.fetchone()
        if not roadmap_row:
            return None

        roadmap_id = roadmap_row["id"]
        tasks_query = """
            SELECT
                id,
                roadmap_id,
                skill_name,
                skill_category,
                module_order,
                task_title,
                task_description,
                resource_url,
                estimated_minutes,
                is_completed,
                completed_at,
                notes,
                prerequisites
            FROM roadmap_tasks
            WHERE roadmap_id = ?
            ORDER BY module_order ASC, task_title ASC
        """
        task_rows = conn.execute(tasks_query, (roadmap_id,)).fetchall()

    tasks = []
    for r in task_rows:
        prereqs = r["prerequisites"]
        if prereqs:
            try:
                prereqs = json.loads(prereqs)
            except Exception:
                pass
        tasks.append({
            "id": r["id"],
            "roadmap_id": r["roadmap_id"],
            "skill_name": r["skill_name"],
            "skill_category": r["skill_category"],
            "module_order": r["module_order"],
            "task_title": r["task_title"],
            "task_description": r["task_description"],
            "resource_url": r["resource_url"],
            "estimated_minutes": r["estimated_minutes"],
            "is_completed": bool(r["is_completed"]),
            "completed_at": r["completed_at"],
            "notes": r["notes"],
            "prerequisites": prereqs,
        })

    metadata = {}
    if roadmap_row["roadmap_metadata"]:
        try:
            metadata = json.loads(roadmap_row["roadmap_metadata"])
        except Exception:
            metadata = {}

    return {
        "id": roadmap_row["id"],
        "session_id": roadmap_row["session_id"],
        "title": roadmap_row["title"],
        "target_role": roadmap_row["target_role"],
        "total_estimated_hours": roadmap_row["total_estimated_hours"],
        "status": roadmap_row["status"],
        "roadmap_metadata": metadata,
        "created_at": roadmap_row["created_at"],
        "updated_at": roadmap_row["updated_at"],
        "tasks": tasks,
    }


def get_roadmap_task_by_id(
    task_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve an individual roadmap task by its UUID."""
    if not is_valid_uuid(task_id):
        return None

    query = """
        SELECT
            id,
            roadmap_id,
            skill_name,
            skill_category,
            module_order,
            task_title,
            task_description,
            resource_url,
            estimated_minutes,
            is_completed,
            completed_at,
            notes,
            prerequisites
        FROM roadmap_tasks
        WHERE id = ?
    """

    with get_db(db_path) as conn:
        cursor = conn.execute(query, (task_id,))
        r = cursor.fetchone()

    if not r:
        return None

    prereqs = r["prerequisites"]
    if prereqs:
        try:
            prereqs = json.loads(prereqs)
        except Exception:
            pass

    return {
        "id": r["id"],
        "roadmap_id": r["roadmap_id"],
        "skill_name": r["skill_name"],
        "skill_category": r["skill_category"],
        "module_order": r["module_order"],
        "task_title": r["task_title"],
        "task_description": r["task_description"],
        "resource_url": r["resource_url"],
        "estimated_minutes": r["estimated_minutes"],
        "is_completed": bool(r["is_completed"]),
        "completed_at": r["completed_at"],
        "notes": r["notes"],
        "prerequisites": prereqs,
    }


def update_roadmap_task(
    task_id: str,
    is_completed: Optional[bool] = None,
    notes: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update completion status or notes of a task.
    Sets completed_at timestamp on completion and updates parent roadmap updated_at.
    """
    if not is_valid_uuid(task_id):
        return None

    existing = get_roadmap_task_by_id(task_id, db_path=db_path)
    if not existing:
        return None

    now = datetime.utcnow().isoformat()
    new_completed = existing["is_completed"] if is_completed is None else bool(is_completed)
    completed_at = existing["completed_at"]

    if is_completed is not None:
        if is_completed:
            completed_at = completed_at or now
        else:
            completed_at = None

    new_notes = existing["notes"] if notes is None else notes

    query = """
        UPDATE roadmap_tasks
        SET is_completed = ?,
            completed_at = ?,
            notes = ?
        WHERE id = ?
    """

    with get_db(db_path) as conn:
        conn.execute(query, (1 if new_completed else 0, completed_at, new_notes, task_id))
        # Update parent roadmap updated_at timestamp
        conn.execute(
            "UPDATE learning_roadmaps SET updated_at = ? WHERE id = ?",
            (now, existing["roadmap_id"]),
        )

    return get_roadmap_task_by_id(task_id, db_path=db_path)


def get_roadmap_progress(
    session_id: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Calculate and return comprehensive progress metrics for an analysis session's roadmap.
    Recalculates remaining estimated hours, completion percentage, and remaining timeline.
    """
    if not is_valid_uuid(session_id):
        return None

    roadmap = get_learning_roadmap_by_session(session_id, db_path=db_path)
    if not roadmap:
        return None

    tasks = roadmap.get("tasks", [])
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["is_completed"])
    pending_tasks = total_tasks - completed_tasks

    completion_percentage = (
        round((completed_tasks / total_tasks) * 100.0, 2) if total_tasks > 0 else 0.0
    )

    completed_minutes = sum(t["estimated_minutes"] for t in tasks if t["is_completed"])
    pending_minutes = sum(t["estimated_minutes"] for t in tasks if not t["is_completed"])
    total_minutes = completed_minutes + pending_minutes

    completed_hours = round(completed_minutes / 60.0, 2)
    remaining_hours = round(pending_minutes / 60.0, 2)
    total_hours = round(total_minutes / 60.0, 2)

    # Fetch user preferences for weekly hours calculation
    prefs = get_user_preferences(session_id, db_path=db_path) or {}
    weekly_hours = prefs.get("weekly_hours", 10)
    target_timeline = prefs.get("target_timeline_weeks")

    # Adaptive duration calculation with 15% planning buffer
    buffer_multiplier = 1.15
    if weekly_hours > 0:
        remaining_weeks = round((remaining_hours * buffer_multiplier) / float(weekly_hours), 2)
    else:
        remaining_weeks = 0.0

    # Skill breakdown
    skill_stats: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        s_name = t["skill_name"]
        if s_name not in skill_stats:
            skill_stats[s_name] = {
                "skill": s_name,
                "category": t["skill_category"],
                "total_tasks": 0,
                "completed_tasks": 0,
                "total_minutes": 0,
                "completed_minutes": 0,
            }
        skill_stats[s_name]["total_tasks"] += 1
        skill_stats[s_name]["total_minutes"] += t["estimated_minutes"]
        if t["is_completed"]:
            skill_stats[s_name]["completed_tasks"] += 1
            skill_stats[s_name]["completed_minutes"] += t["estimated_minutes"]

    skill_breakdown = []
    for s_name, stats in skill_stats.items():
        s_total = stats["total_tasks"]
        s_done = stats["completed_tasks"]
        s_pct = round((s_done / s_total) * 100.0, 2) if s_total > 0 else 0.0
        s_rem_hrs = round((stats["total_minutes"] - stats["completed_minutes"]) / 60.0, 2)
        skill_breakdown.append({
            "skill": s_name,
            "category": stats["category"],
            "total_tasks": s_total,
            "completed_tasks": s_done,
            "completion_percentage": s_pct,
            "remaining_hours": s_rem_hrs,
        })

    # Check feasibility if target timeline was provided
    timeline_feasibility = "n/a"
    feasibility_note = None
    if target_timeline:
        if remaining_weeks <= target_timeline:
            timeline_feasibility = "achievable"
            feasibility_note = (
                f"Remaining learning workload ({remaining_hours}h) is achievable within your target of "
                f"{target_timeline} weeks at {weekly_hours} hours/week."
            )
        else:
            timeline_feasibility = "unrealistic"
            needed_weekly = round((remaining_hours * buffer_multiplier) / float(target_timeline), 1)
            feasibility_note = (
                f"Target timeline of {target_timeline} weeks is unrealistic for {remaining_hours} remaining "
                f"hours at {weekly_hours}h/week (requires ~{remaining_weeks} weeks with buffer). "
                f"You would need ~{needed_weekly} hours/week to finish within target."
            )

    return {
        "session_id": session_id,
        "roadmap_id": roadmap["id"],
        "roadmap_title": roadmap["title"],
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "completion_percentage": completion_percentage,
        "completed_learning_hours": completed_hours,
        "remaining_estimated_hours": remaining_hours,
        "total_estimated_hours": total_hours,
        "weekly_hours": weekly_hours,
        "estimated_remaining_weeks": remaining_weeks,
        "target_timeline_weeks": target_timeline,
        "timeline_feasibility": timeline_feasibility,
        "feasibility_note": feasibility_note,
        "status": "completed" if (total_tasks > 0 and completed_tasks == total_tasks) else "in_progress",
        "skills_progress": skill_breakdown,
    }
