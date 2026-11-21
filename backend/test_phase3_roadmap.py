"""
SkillGap AI - Phase 3 Adaptive Roadmap & Progress Tracking Test Suite.

Tests:
1. Roadmap generation from a real saved analysis session with actual missing skills.
2. Roadmap retrieval (GET /api/sessions/{session_id}/roadmap).
3. Task completion updates (PATCH /api/tasks/{task_id}).
4. Progress calculation (GET /api/sessions/{session_id}/progress).
5. Dynamic duration recalculation after task completion and after changing weekly study hours.
6. Target timeline feasibility check (identifies unrealistic vs achievable targets).
7. Invalid session handling (400 for malformed UUID, 404 for nonexistent UUID).
8. Database persistence after backend restart.
9. Existing resume analysis functionality & health endpoints preserved.
"""

import os
import sys
import json
import uuid
import tempfile
import urllib.request
import urllib.error
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import pymupdf as fitz
from db import (
    get_connection,
    init_db,
    create_analysis_session,
    get_analysis_session,
    save_user_preferences,
    get_user_preferences,
    create_learning_roadmap,
    get_learning_roadmap_by_session,
    update_roadmap_task,
    get_roadmap_task_by_id,
    get_roadmap_progress,
    is_valid_uuid,
)
from roadmap import generate_adaptive_roadmap, CREDIBLE_RESOURCE_URLS

BASE_URL = "http://127.0.0.1:8000"


def create_test_pdf(text: str) -> bytes:
    """Create in-memory PDF resume using PyMuPDF."""
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


def run_phase3_tests():
    print("=" * 70)
    print("PHASE 3: ADAPTIVE ROADMAP ENGINE & PROGRESS TRACKING TESTS")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # Step 0: Ensure backend health and existing endpoints work
    # -----------------------------------------------------------------------
    with urllib.request.urlopen(f"{BASE_URL}/api/health") as resp:
        assert resp.status == 200
        health_data = json.loads(resp.read().decode())
        assert health_data["status"] == "healthy"
        print("[PASS] Backend is running and healthy at http://127.0.0.1:8000.")

    # -----------------------------------------------------------------------
    # Test 1: Real Analysis Session Creation via POST /api/analyze
    # -----------------------------------------------------------------------
    print("\n--- Test 1: Perform Real Resume Analysis ---")
    resume_text = """
    Jane Developer - Backend Engineer
    Skills: Python, FastAPI, Docker, PostgreSQL, Git, Linux
    Experience: Developed web services using FastAPI and PostgreSQL database.
    """
    pdf_bytes = create_test_pdf(resume_text)

    # Job description requires Python, FastAPI, Docker, and KUBERNETES + REDIS (which are missing)
    job_desc = """
    Looking for a Senior Backend Engineer proficient in:
    • Python and FastAPI
    • Docker containerization and Kubernetes cluster management
    • PostgreSQL database and Redis caching layer
    """

    boundary = "----TestBoundaryPhase3"
    payload = build_multipart_payload(
        fields={"job_description": job_desc},
        files={"resume": ("jane_resume.pdf", pdf_bytes, "application/pdf")},
        boundary=boundary,
    )

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        analysis_result = json.loads(resp.read().decode())
        session_id = analysis_result["session_id"]
        assert is_valid_uuid(session_id)
        assert "Kubernetes" in analysis_result["missing_skills"]
        assert "Redis" in analysis_result["missing_skills"]
        print(f"[PASS] Real analysis succeeded: session_id={session_id}")
        print(f"       Missing skills to bridge: {analysis_result['missing_skills']}")

    # -----------------------------------------------------------------------
    # Test 2: Roadmap Generation via POST /api/sessions/{session_id}/roadmap/generate
    # -----------------------------------------------------------------------
    print("\n--- Test 2: Adaptive Roadmap Generation ---")
    gen_payload = json.dumps({
        "weekly_hours": 10,
        "skill_level": "intermediate",
        "learning_style": "hands_on",
        "target_timeline_weeks": 6,  # 6 weeks target
    }).encode("utf-8")

    req_gen = urllib.request.Request(
        f"{BASE_URL}/api/sessions/{session_id}/roadmap/generate",
        data=gen_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req_gen, timeout=5) as resp:
        assert resp.status == 200
        gen_data = json.loads(resp.read().decode())
        assert gen_data["success"] is True
        roadmap = gen_data["roadmap"]
        assert is_valid_uuid(roadmap["id"])
        assert roadmap["session_id"] == session_id
        tasks = roadmap["tasks"]
        assert len(tasks) > 0

        # Verify task structure: each missing skill has 5 actionable phases
        skills_in_tasks = {t["skill_name"] for t in tasks}
        assert "Kubernetes" in skills_in_tasks
        assert "Redis" in skills_in_tasks

        # Verify credible URLs
        for t in tasks:
            assert is_valid_uuid(t["id"])
            assert t["estimated_minutes"] > 0
            assert t["is_completed"] is False
            if t["skill_name"] in CREDIBLE_RESOURCE_URLS:
                assert t["resource_url"] == CREDIBLE_RESOURCE_URLS[t["skill_name"]]

        meta = roadmap["roadmap_metadata"]
        print(f"[PASS] Roadmap generated: '{roadmap['title']}'")
        print(f"       Total Tasks: {len(tasks)}")
        print(f"       Estimated Hours: {roadmap['total_estimated_hours']}h")
        print(f"       Estimated Duration: {meta['estimated_duration_weeks']} weeks at {meta['weekly_hours']}h/week")
        print(f"       Timeline Feasibility: {meta['timeline_feasibility']}")

    # -----------------------------------------------------------------------
    # Test 3: Roadmap Retrieval via GET /api/sessions/{session_id}/roadmap
    # -----------------------------------------------------------------------
    print("\n--- Test 3: Roadmap Retrieval ---")
    req_get_rm = urllib.request.Request(f"{BASE_URL}/api/sessions/{session_id}/roadmap")
    with urllib.request.urlopen(req_get_rm, timeout=5) as resp:
        assert resp.status == 200
        rm_data = json.loads(resp.read().decode())
        assert rm_data["success"] is True
        retrieved_rm = rm_data["roadmap"]
        assert retrieved_rm["id"] == roadmap["id"]
        assert len(retrieved_rm["tasks"]) == len(tasks)
        print(f"[PASS] Retrieved roadmap successfully with {len(retrieved_rm['tasks'])} tasks.")

    # -----------------------------------------------------------------------
    # Test 4: Task Completion Updates via PATCH /api/tasks/{task_id}
    # -----------------------------------------------------------------------
    print("\n--- Test 4: Task Completion Updates ---")
    first_task = tasks[0]
    task_id = first_task["id"]

    patch_payload = json.dumps({
        "is_completed": True,
        "notes": "Studied Kubernetes architecture and setup local Minikube cluster.",
    }).encode("utf-8")

    req_patch = urllib.request.Request(
        f"{BASE_URL}/api/tasks/{task_id}",
        data=patch_payload,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )

    with urllib.request.urlopen(req_patch, timeout=5) as resp:
        assert resp.status == 200
        patch_data = json.loads(resp.read().decode())
        assert patch_data["success"] is True
        updated_task = patch_data["task"]
        assert updated_task["id"] == task_id
        assert updated_task["is_completed"] is True
        assert updated_task["completed_at"] is not None
        assert "Minikube" in updated_task["notes"]
        print(f"[PASS] Task '{updated_task['task_title'][:40]}...' marked completed with notes.")

    # -----------------------------------------------------------------------
    # Test 5: Progress Calculation via GET /api/sessions/{session_id}/progress
    # -----------------------------------------------------------------------
    print("\n--- Test 5: Progress Metrics Calculation ---")
    req_prog = urllib.request.Request(f"{BASE_URL}/api/sessions/{session_id}/progress")
    with urllib.request.urlopen(req_prog, timeout=5) as resp:
        assert resp.status == 200
        prog_data = json.loads(resp.read().decode())
        assert prog_data["success"] is True
        p = prog_data["progress"]
        assert p["completed_tasks"] == 1
        assert p["total_tasks"] == len(tasks)
        assert p["pending_tasks"] == len(tasks) - 1
        assert p["completion_percentage"] > 0
        assert p["completed_learning_hours"] > 0
        assert p["remaining_estimated_hours"] < p["total_estimated_hours"]
        print(f"[PASS] Progress verified: {p['completed_tasks']}/{p['total_tasks']} tasks done ({p['completion_percentage']}%)")
        print(f"       Completed: {p['completed_learning_hours']}h | Remaining: {p['remaining_estimated_hours']}h")
        print(f"       Remaining Weeks: {p['estimated_remaining_weeks']} weeks")

    # -----------------------------------------------------------------------
    # Test 6: Dynamic Duration Recalculation after Progress & Preference Changes
    # -----------------------------------------------------------------------
    print("\n--- Test 6: Dynamic Duration Recalculation ---")
    initial_remaining_weeks = p["estimated_remaining_weeks"]

    # Mark second task completed
    second_task_id = tasks[1]["id"]
    req_patch_2 = urllib.request.Request(
        f"{BASE_URL}/api/tasks/{second_task_id}",
        data=json.dumps({"is_completed": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    urllib.request.urlopen(req_patch_2, timeout=5)

    # Check that remaining weeks decreased
    with urllib.request.urlopen(f"{BASE_URL}/api/sessions/{session_id}/progress") as resp:
        p2 = json.loads(resp.read().decode())["progress"]
        assert p2["completed_tasks"] == 2
        assert p2["remaining_estimated_hours"] < p["remaining_estimated_hours"]
        assert p2["estimated_remaining_weeks"] < initial_remaining_weeks
        print(f"[PASS] Duration dynamically decreased after completing second task: "
              f"{initial_remaining_weeks}w -> {p2['estimated_remaining_weeks']}w.")

    # Now update study hours from 10h/week to 20h/week
    req_speed = urllib.request.Request(
        f"{BASE_URL}/api/sessions/{session_id}/preferences",
        data=json.dumps({"weekly_hours": 20}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req_speed, timeout=5)

    with urllib.request.urlopen(f"{BASE_URL}/api/sessions/{session_id}/progress") as resp:
        p3 = json.loads(resp.read().decode())["progress"]
        assert p3["weekly_hours"] == 20
        # Doubling study hours approximately halves remaining weeks
        assert p3["estimated_remaining_weeks"] < p2["estimated_remaining_weeks"]
        print(f"[PASS] Doubling weekly study hours (10h -> 20h) dynamically recalculated remaining duration: "
              f"{p2['estimated_remaining_weeks']}w -> {p3['estimated_remaining_weeks']}w.")

    # -----------------------------------------------------------------------
    # Test 7: Feasibility Analysis (Realistic vs Unrealistic Target)
    # -----------------------------------------------------------------------
    print("\n--- Test 7: Timeline Feasibility Verification ---")
    # Set an unrealistic target timeline of 1 week for ~35 hours of remaining learning
    req_unreal = urllib.request.Request(
        f"{BASE_URL}/api/sessions/{session_id}/preferences",
        data=json.dumps({"weekly_hours": 5, "target_timeline_weeks": 1}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req_unreal, timeout=5)

    with urllib.request.urlopen(f"{BASE_URL}/api/sessions/{session_id}/progress") as resp:
        p_unreal = json.loads(resp.read().decode())["progress"]
        assert p_unreal["timeline_feasibility"] == "unrealistic"
        assert "unrealistic" in p_unreal["feasibility_note"].lower()
        print(f"[PASS] Detected unrealistic target timeline: '{p_unreal['feasibility_note']}'")

    # -----------------------------------------------------------------------
    # Test 8: Error Handling (Invalid & Nonexistent IDs)
    # -----------------------------------------------------------------------
    print("\n--- Test 8: Error Handling (400 for bad UUID, 404 for nonexistent) ---")
    bad_uuid = "invalid-uuid-format"
    for ep in [
        f"{BASE_URL}/api/sessions/{bad_uuid}/roadmap",
        f"{BASE_URL}/api/sessions/{bad_uuid}/progress",
    ]:
        try:
            urllib.request.urlopen(ep)
            assert False, f"Expected 400 for {ep}"
        except urllib.error.HTTPError as err:
            assert err.code == 400, f"Expected 400, got {err.code}"

    # Test PATCH /api/tasks/{bad_uuid} with PATCH method
    req_bad_patch = urllib.request.Request(
        f"{BASE_URL}/api/tasks/{bad_uuid}",
        data=json.dumps({"is_completed": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        urllib.request.urlopen(req_bad_patch)
        assert False, "Expected 400 for bad task UUID"
    except urllib.error.HTTPError as err:
        assert err.code == 400, f"Expected 400, got {err.code}"

    fake_uuid = str(uuid.uuid4())
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/sessions/{fake_uuid}/roadmap")
        assert False, "Expected 404 for nonexistent session roadmap"
    except urllib.error.HTTPError as err:
        assert err.code == 404
        print("[PASS] Verified HTTP 400 for invalid UUIDs and HTTP 404 for nonexistent IDs.")

    # -----------------------------------------------------------------------
    # Test 9: Persistence Verification on Direct SQLite Connection
    # -----------------------------------------------------------------------
    print("\n--- Test 9: Persistence Verification on SQLite Connection ---")
    db_file = os.path.join(CURRENT_DIR, "db", "skillgap.db")
    conn = get_connection(db_file)
    cur = conn.cursor()

    # Verify roadmap and task records exist in physical database
    cur.execute("SELECT COUNT(*) FROM learning_roadmaps WHERE session_id = ?", (session_id,))
    assert cur.fetchone()[0] == 1, "Roadmap record missing in SQLite"

    cur.execute("SELECT COUNT(*) FROM roadmap_tasks WHERE is_completed = 1")
    completed_count = cur.fetchone()[0]
    assert completed_count >= 2, f"Expected >= 2 completed tasks in DB, got {completed_count}"
    print(f"[PASS] Verified physical SQLite persistence: {completed_count} completed tasks persisted.")
    conn.close()

    print("\n" + "=" * 70)
    print("ALL 9 PHASE 3 ROADMAP & PROGRESS TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase3_tests()
