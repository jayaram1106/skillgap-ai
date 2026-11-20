"""
SkillGap AI - Database Module.
"""

from .database import (
    get_db,
    get_connection,
    init_db,
    get_db_path,
    DEFAULT_DB_PATH,
)
from .repository import (
    is_valid_uuid,
    create_analysis_session,
    get_analysis_session,
    list_analysis_sessions,
    save_user_preferences,
    get_user_preferences,
)

__all__ = [
    "get_db",
    "get_connection",
    "init_db",
    "get_db_path",
    "DEFAULT_DB_PATH",
    "is_valid_uuid",
    "create_analysis_session",
    "get_analysis_session",
    "list_analysis_sessions",
    "save_user_preferences",
    "get_user_preferences",
]
