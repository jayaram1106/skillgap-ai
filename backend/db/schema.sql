-- ===========================================================================
-- SkillGap AI - Relational Database Schema (SQLite)
--
-- Tables:
--   1. analysis_sessions: Stored skill gap analysis results (NO raw PDFs or resume text)
--   2. user_preferences: Session-based learning preferences with future user_id hook
--   3. learning_roadmaps: Generated modular learning roadmaps for missing skills
--   4. roadmap_tasks: Granular trackable tasks and completion progress
-- ===========================================================================

-- 1. Analysis Sessions
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    job_title TEXT,
    job_description_snippet TEXT NOT NULL,
    match_percentage REAL NOT NULL CHECK (match_percentage >= 0.0 AND match_percentage <= 100.0),
    summary TEXT NOT NULL,
    required_skills TEXT NOT NULL,     -- JSON array of strings
    resume_skills TEXT NOT NULL,       -- JSON array of strings
    matched_skills TEXT NOT NULL,      -- JSON array of strings
    missing_skills TEXT NOT NULL,      -- JSON array of strings
    additional_skills TEXT NOT NULL,   -- JSON array of strings
    score_explanation TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analysis_sessions_created_at 
    ON analysis_sessions(created_at DESC);

-- 2. User Learning Preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    user_id TEXT,                      -- Nullable, allows future auth/account binding without schema migration
    weekly_hours INTEGER NOT NULL DEFAULT 10 CHECK (weekly_hours > 0 AND weekly_hours <= 168),
    skill_level TEXT NOT NULL DEFAULT 'intermediate' CHECK (skill_level IN ('beginner', 'intermediate', 'advanced')),
    learning_style TEXT NOT NULL DEFAULT 'hands_on' CHECK (learning_style IN ('hands_on', 'video_first', 'reading_docs', 'project_based')),
    target_timeline_weeks INTEGER CHECK (target_timeline_weeks IS NULL OR target_timeline_weeks > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_session_id 
    ON user_preferences(session_id);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id 
    ON user_preferences(user_id);

-- 3. Learning Roadmaps (Optional relationship to analysis_sessions)
CREATE TABLE IF NOT EXISTS learning_roadmaps (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    target_role TEXT,
    total_estimated_hours REAL NOT NULL DEFAULT 0.0 CHECK (total_estimated_hours >= 0.0),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    roadmap_metadata TEXT,             -- JSON object for milestones and modules
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_learning_roadmaps_session_id 
    ON learning_roadmaps(session_id);

CREATE INDEX IF NOT EXISTS idx_learning_roadmaps_status 
    ON learning_roadmaps(status);

-- 4. Roadmap Tasks (Trackable skill progress & tasks)
CREATE TABLE IF NOT EXISTS roadmap_tasks (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    skill_category TEXT NOT NULL,
    module_order INTEGER NOT NULL DEFAULT 1 CHECK (module_order >= 1),
    task_title TEXT NOT NULL,
    task_description TEXT,
    resource_url TEXT,
    estimated_minutes INTEGER NOT NULL DEFAULT 60 CHECK (estimated_minutes > 0),
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1)),
    completed_at TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (roadmap_id) REFERENCES learning_roadmaps(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_roadmap_id 
    ON roadmap_tasks(roadmap_id);

CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_skill_name 
    ON roadmap_tasks(skill_name);

CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_is_completed 
    ON roadmap_tasks(is_completed);
