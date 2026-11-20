"""
SkillGap AI - Comprehensive Database & API Integration Test Suite.

Tests:
1. Database initialization & PRAGMAs (WAL mode, foreign keys, table creation)
2. Creating and retrieving analysis sessions
3. Persistence after backend restart (connection teardown and reconnection)
4. Invalid session IDs & UUID validation
5. Foreign-key enforcement & cascading deletion
6. Existing POST /api/analyze functionality with real PDF & job description
7. Strict privacy: No PDF binary or raw resume text persisted in SQLite
"""

import os
import sys
import json
import uuid
import tempfile
import sqlite3
import urllib.request
import urllib.error

# Ensure backend directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import pymupdf as fitz
from db import (
    init_db,
    get_connection,
    create_analysis_session,
    get_analysis_session,
    list_analysis_sessions,
    save_user_preferences,
    get_user_preferences,
    is_valid_uuid,
)


def create_test_pdf(text: str) -> bytes:
    """Create a valid in-memory PDF with PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def build_multipart_payload(fields: dict, files: dict, boundary: str) -> bytes:
    """Construct multipart/form-data payload."""
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))
    for name, (filename, file_bytes, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)


def run_database_tests():
    print("=" * 70)
    print("SKILLGAP AI - SQLITE DATABASE INTEGRATION TEST SUITE")
    print("=" * 70)

    # Use a clean temporary SQLite database file for isolation
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        test_db_path = tf.name

    try:
        # -------------------------------------------------------------------
        # Test 1: Database Initialization
        # -------------------------------------------------------------------
        print("\n--- Test 1: Database Initialization ---")
        init_db(test_db_path)

        conn = get_connection(test_db_path)
        cursor = conn.cursor()

        # Verify PRAGMA settings
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        assert fk_status == 1, f"Expected foreign_keys=1, got {fk_status}"

        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0].lower()
        assert journal_mode == "wal", f"Expected journal_mode=wal, got {journal_mode}"

        cursor.execute("PRAGMA busy_timeout;")
        busy_timeout = cursor.fetchone()[0]
        assert busy_timeout >= 5000, f"Expected busy_timeout>=5000, got {busy_timeout}"

        # Verify all 4 required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {
            "analysis_sessions",
            "user_preferences",
            "learning_roadmaps",
            "roadmap_tasks",
        }
        for t in required_tables:
            assert t in tables, f"Missing required table: {t}"
        print(f"[PASS] Database initialized with WAL mode, foreign keys ON, and all required tables: {sorted(list(required_tables))}")
        conn.close()

        # -------------------------------------------------------------------
        # Test 2: Creating and Retrieving Analysis Sessions
        # -------------------------------------------------------------------
        print("\n--- Test 2: Creating and Retrieving Analysis Sessions ---")
        req_skills = ["FastAPI", "Python", "Kubernetes", "Docker"]
        res_skills = ["FastAPI", "Python", "Docker", "PostgreSQL"]
        matched = ["Docker", "FastAPI", "Python"]
        missing = ["Kubernetes"]
        additional = ["PostgreSQL"]

        session_id = create_analysis_session(
            match_percentage=75.0,
            summary="Matched 3 of 4 required skills. Missing: Kubernetes.",
            required_skills=req_skills,
            resume_skills=res_skills,
            matched_skills=matched,
            missing_skills=missing,
            additional_skills=additional,
            score_explanation="(3/4) * 100 = 75%",
            job_description_snippet="Senior Backend Engineer needed with FastAPI and Kubernetes.",
            job_title="Senior Backend Engineer",
            db_path=test_db_path,
        )

        assert is_valid_uuid(session_id), f"Expected valid UUID string, got {session_id}"
        print(f"[PASS] Successfully created session with UUID: {session_id}")

        retrieved = get_analysis_session(session_id, db_path=test_db_path)
        assert retrieved is not None, "Failed to retrieve saved session"
        assert retrieved["id"] == session_id
        assert retrieved["match_percentage"] == 75.0
        assert retrieved["matched_skills"] == matched
        assert retrieved["missing_skills"] == missing
        assert retrieved["additional_skills"] == additional
        assert retrieved["job_title"] == "Senior Backend Engineer"
        print("[PASS] Retrieved session matches all inserted values and parsed JSON lists.")

        # -------------------------------------------------------------------
        # Test 3: Persistence After Backend Restart (Teardown & Reconnect)
        # -------------------------------------------------------------------
        print("\n--- Test 3: Persistence After Backend Restart ---")
        # Simulating restart by completely clearing any open references and creating a brand new connection
        new_conn = get_connection(test_db_path)
        row = new_conn.execute("SELECT COUNT(*) FROM analysis_sessions WHERE id = ?", (session_id,)).fetchone()
        assert row[0] == 1, "Session record lost after connection teardown!"
        new_conn.close()
        print("[PASS] Session record successfully persisted and verified on a fresh connection.")

        # -------------------------------------------------------------------
        # Test 4: Invalid Session IDs & UUID Validation
        # -------------------------------------------------------------------
        print("\n--- Test 4: Invalid Session IDs & UUID Validation ---")
        invalid_ids = ["not-a-uuid", "12345", "'; DROP TABLE analysis_sessions; --", "", None]
        for bad_id in invalid_ids:
            assert not is_valid_uuid(bad_id), f"Should not validate as UUID: {bad_id}"
            assert get_analysis_session(bad_id, db_path=test_db_path) is None

        # Valid UUID format that does not exist in the database
        nonexistent_uuid = str(uuid.uuid4())
        assert is_valid_uuid(nonexistent_uuid)
        assert get_analysis_session(nonexistent_uuid, db_path=test_db_path) is None
        print("[PASS] UUID validation and non-existent ID queries handled safely.")

        # -------------------------------------------------------------------
        # Test 5: Foreign-Key Enforcement & Cascading Deletion
        # -------------------------------------------------------------------
        print("\n--- Test 5: Foreign-Key Enforcement & Cascading Deletion ---")
        fake_session_id = str(uuid.uuid4())
        try:
            save_user_preferences(
                session_id=fake_session_id,
                weekly_hours=10,
                skill_level="intermediate",
                learning_style="hands_on",
                db_path=test_db_path,
            )
            assert False, "Should have failed with IntegrityError (Foreign Key)"
        except sqlite3.IntegrityError:
            print("[PASS] Foreign key enforcement prevented inserting orphan user preferences.")

        # Insert valid preferences for existing session
        prefs = save_user_preferences(
            session_id=session_id,
            weekly_hours=12,
            skill_level="advanced",
            learning_style="project_based",
            target_timeline_weeks=None,  # Optional: dynamic calculation
            db_path=test_db_path,
        )
        assert prefs["weekly_hours"] == 12
        assert prefs["target_timeline_weeks"] is None

        # Verify cascading deletion: deleting session must delete preferences
        with get_connection(test_db_path) as c:
            c.execute("DELETE FROM analysis_sessions WHERE id = ?", (session_id,))
            c.commit()

        assert get_analysis_session(session_id, db_path=test_db_path) is None
        assert get_user_preferences(session_id, db_path=test_db_path) is None
        print("[PASS] Cascading delete verified: deleting session automatically removed child preferences.")

        # -------------------------------------------------------------------
        # Test 6: Strict Privacy: No PDF Binary or Raw Resume Text Persisted
        # -------------------------------------------------------------------
        print("\n--- Test 6: Strict Privacy (No PDF or Resume Text Persisted) ---")
        # Check table schema columns
        conn = get_connection(test_db_path)
        col_cursor = conn.execute("PRAGMA table_info(analysis_sessions);")
        columns = [row["name"] for row in col_cursor.fetchall()]
        forbidden_cols = ["pdf", "pdf_bytes", "resume", "resume_text", "raw_text", "evidence"]
        for fc in forbidden_cols:
            assert fc not in columns, f"Forbidden column found in analysis_sessions: {fc}"
        print(f"[PASS] Confirmed database schema columns exclude raw text and PDF storage: {columns}")
        conn.close()

    finally:
        # Cleanup temporary test files
        for ext in ["", "-wal", "-shm"]:
            f = test_db_path + ext
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass

    # -----------------------------------------------------------------------
    # Test 7: Live API Integration Tests with Running FastAPI Backend
    # -----------------------------------------------------------------------
    print("\n--- Test 7: Live API Integration (POST /api/analyze & GET /api/sessions) ---")
    base_url = "http://127.0.0.1:8000"

    # Create test PDF with sensitive canary text that MUST NOT be persisted
    canary_text = "SECRET_CANARY_CONTACT_INFO_555_0199_DO_NOT_PERSIST"
    sample_resume = f"""
    Candidate: Jane Doe
    Contact: {canary_text}
    Skills: Python, FastAPI, Docker, PostgreSQL, Redis, Linux
    Experience: Built high-performance microservices using FastAPI and Docker.
    """
    pdf_bytes = create_test_pdf(sample_resume)

    job_description = """
    We need a Senior Python Backend Developer with strong skills in:
    • Python and FastAPI
    • Docker and Kubernetes
    • PostgreSQL database design
    """

    boundary = "----TestDatabaseBoundary999"
    payload = build_multipart_payload(
        fields={"job_description": job_description},
        files={"resume": ("canary_resume.pdf", pdf_bytes, "application/pdf")},
        boundary=boundary,
    )

    req = urllib.request.Request(
        f"{base_url}/api/analyze",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["success"] is True
        assert "session_id" in data, "session_id must be returned in response"
        live_session_id = data["session_id"]
        assert is_valid_uuid(live_session_id), f"Invalid session_id UUID: {live_session_id}"
        assert data["match_percentage"] > 0
        assert "FastAPI" in data["matched_skills"]
        assert "Kubernetes" in data["missing_skills"]
        print(f"[PASS] POST /api/analyze succeeded. Returned session_id: {live_session_id}")

    # Test GET /api/sessions/{session_id}
    req_get = urllib.request.Request(f"{base_url}/api/sessions/{live_session_id}")
    with urllib.request.urlopen(req_get, timeout=5) as resp:
        assert resp.status == 200
        get_data = json.loads(resp.read().decode())
        assert get_data["success"] is True
        sess = get_data["session"]
        assert sess["id"] == live_session_id
        assert "FastAPI" in sess["matched_skills"]
        assert "Kubernetes" in sess["missing_skills"]
        print(f"[PASS] GET /api/sessions/{live_session_id} successfully retrieved persisted session.")

    # Test GET /api/sessions list
    req_list = urllib.request.Request(f"{base_url}/api/sessions")
    with urllib.request.urlopen(req_list, timeout=5) as resp:
        assert resp.status == 200
        list_data = json.loads(resp.read().decode())
        assert list_data["success"] is True
        assert list_data["count"] >= 1
        print(f"[PASS] GET /api/sessions successfully listed {list_data['count']} session(s).")

    # Test Preferences endpoint: POST /api/sessions/{session_id}/preferences
    pref_payload = json.dumps({
        "weekly_hours": 15,
        "skill_level": "intermediate",
        "learning_style": "hands_on",
        "target_timeline_weeks": None,
    }).encode("utf-8")

    req_pref = urllib.request.Request(
        f"{base_url}/api/sessions/{live_session_id}/preferences",
        data=pref_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req_pref, timeout=5) as resp:
        assert resp.status == 200
        saved_prefs = json.loads(resp.read().decode())
        assert saved_prefs["success"] is True
        assert saved_prefs["preferences"]["weekly_hours"] == 15
        assert saved_prefs["preferences"]["target_timeline_weeks"] is None
        print(f"[PASS] POST /api/sessions/{live_session_id}/preferences successfully saved learning preferences.")

    # Test 404 for nonexistent session
    nonexistent = str(uuid.uuid4())
    try:
        urllib.request.urlopen(f"{base_url}/api/sessions/{nonexistent}")
        assert False, "Should have returned 404"
    except urllib.error.HTTPError as err:
        assert err.code == 404
        print(f"[PASS] GET /api/sessions/{nonexistent} correctly returned HTTP 404 Not Found.")

    # Test 400 for malformed UUID
    try:
        urllib.request.urlopen(f"{base_url}/api/sessions/not-a-valid-uuid")
        assert False, "Should have returned 400"
    except urllib.error.HTTPError as err:
        assert err.code == 400
        print("[PASS] GET /api/sessions/not-a-valid-uuid correctly returned HTTP 400 Bad Request.")

    # Final check: Verify that the CANARY text is NOT anywhere in the live database
    db_file = os.path.join(CURRENT_DIR, "db", "skillgap.db")
    if os.path.exists(db_file):
        with open(db_file, "rb") as f:
            content = f.read()
            assert canary_text.encode("utf-8") not in content, "SECURITY VIOLATION: Canary text found in database file!"
        print("[PASS] Verified raw PDF binary and resume text (canary text) are NOT present in the database file.")

    print("\n" + "=" * 70)
    print("ALL 7 DATABASE & API INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_database_tests()
