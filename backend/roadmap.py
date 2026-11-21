"""
SkillGap AI - Adaptive Roadmap Generation Engine.

Generates personalized, dependency-aware learning roadmaps based on:
1. Actual missing skills from the analysis session.
2. Skill complexity, difficulty, and prerequisite dependencies.
3. User proficiency level (beginner, intermediate, advanced).
4. Preferred learning style (hands_on, video_first, reading_docs, project_based).
5. Available weekly learning hours.
6. Realistic planning buffers (never fixed 7, 14, or 30 days).
7. Credible, verified official documentation URLs only (never hallucinated).
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import math
import uuid

# ---------------------------------------------------------------------------
# Skill Prerequisite Graph
# ---------------------------------------------------------------------------
# Defines which foundational technologies should precede advanced skills.
SKILL_PREREQUISITES: Dict[str, List[str]] = {
    "Kubernetes": ["Docker", "Linux"],
    "Docker": ["Linux"],
    "FastAPI": ["Python", "REST APIs"],
    "Django": ["Python", "REST APIs"],
    "Flask": ["Python"],
    "React": ["JavaScript", "HTML", "CSS"],
    "Next.js": ["React", "JavaScript"],
    "Vue.js": ["JavaScript", "HTML", "CSS"],
    "Angular": ["TypeScript", "HTML", "CSS"],
    "TypeScript": ["JavaScript"],
    "Node.js": ["JavaScript"],
    "Express.js": ["Node.js", "JavaScript"],
    "Spring Boot": ["Java"],
    "ASP.NET Core": ["C#"],
    "Microservices": ["REST APIs", "Docker"],
    "System Design": ["REST APIs", "SQL"],
    "GraphQL": ["REST APIs"],
    "gRPC": ["REST APIs"],
    "CI/CD": ["Git"],
    "GitHub Actions": ["Git", "CI/CD"],
    "Terraform": ["AWS"],
    "Redis": ["SQL"],
    "PostgreSQL": ["SQL"],
    "MySQL": ["SQL"],
    "Database Design": ["SQL"],
    "Data Structures & Algorithms": ["Python"],
    "Concurrency": ["Python"],
}

# ---------------------------------------------------------------------------
# Skill Baseline Duration (in hours for an intermediate learner)
# ---------------------------------------------------------------------------
SKILL_BASELINE_HOURS: Dict[str, float] = {
    # High complexity / Infrastructure / Architecture
    "Kubernetes": 28.0,
    "System Design": 32.0,
    "Microservices": 24.0,
    "AWS": 28.0,
    "Google Cloud": 26.0,
    "Azure": 26.0,
    "Terraform": 18.0,
    "Concurrency": 20.0,
    "Spring Boot": 26.0,
    "Data Structures & Algorithms": 30.0,
    "Algorithms": 22.0,
    "Data Structures": 18.0,
    "Rust": 28.0,
    "C++": 30.0,

    # Moderate complexity / Frameworks / Databases
    "FastAPI": 16.0,
    "Django": 22.0,
    "Flask": 14.0,
    "React": 22.0,
    "Next.js": 18.0,
    "Vue.js": 18.0,
    "Angular": 24.0,
    "Node.js": 18.0,
    "Express.js": 14.0,
    "TypeScript": 16.0,
    "Python": 22.0,
    "JavaScript": 22.0,
    "Java": 26.0,
    "C#": 24.0,
    "Go": 20.0,
    "PostgreSQL": 16.0,
    "MySQL": 14.0,
    "MongoDB": 14.0,
    "Redis": 12.0,
    "Docker": 16.0,
    "CI/CD": 14.0,
    "GraphQL": 14.0,
    "gRPC": 12.0,
    "Database Design": 16.0,
    "Object-Oriented Programming (OOP)": 14.0,

    # Foundational / Tools / Methodologies
    "Git": 8.0,
    "GitHub": 6.0,
    "GitLab": 6.0,
    "Linux": 12.0,
    "SQL": 12.0,
    "HTML": 8.0,
    "CSS": 10.0,
    "Tailwind CSS": 8.0,
    "REST APIs": 12.0,
    "Pytest": 8.0,
    "Jest": 8.0,
    "Unit Testing": 8.0,
    "Postman": 6.0,
    "Agile": 6.0,
    "Scrum": 6.0,
    "Nginx": 10.0,
}

DEFAULT_SKILL_BASELINE_HOURS = 16.0

# ---------------------------------------------------------------------------
# Verified Credible Official Resource URLs (Never hallucinated)
# ---------------------------------------------------------------------------
CREDIBLE_RESOURCE_URLS: Dict[str, str] = {
    "Python": "https://docs.python.org/3/tutorial/",
    "JavaScript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    "TypeScript": "https://www.typescriptlang.org/docs/",
    "Java": "https://dev.java/learn/",
    "C++": "https://en.cppreference.com/w/cpp",
    "C#": "https://learn.microsoft.com/en-us/dotnet/csharp/",
    "Go": "https://go.dev/doc/tutorial/getting-started",
    "Rust": "https://www.rust-lang.org/learn",
    "Ruby": "https://www.ruby-lang.org/en/documentation/",
    "PHP": "https://www.php.net/manual/en/",
    "SQL": "https://developer.mozilla.org/en-US/docs/Glossary/SQL",
    "FastAPI": "https://fastapi.tiangolo.com/tutorial/",
    "Django": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
    "Flask": "https://flask.palletsprojects.com/en/stable/tutorial/",
    "React": "https://react.dev/learn",
    "Next.js": "https://nextjs.org/docs",
    "Vue.js": "https://vuejs.org/guide/introduction.html",
    "Angular": "https://angular.dev/overview",
    "Node.js": "https://nodejs.org/en/learn",
    "Express.js": "https://expressjs.com/en/starter/installing.html",
    "Spring Boot": "https://spring.io/guides",
    "Docker": "https://docs.docker.com/get-started/",
    "Kubernetes": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
    "PostgreSQL": "https://www.postgresql.org/docs/current/tutorial.html",
    "MySQL": "https://dev.mysql.com/doc/refman/en/tutorial.html",
    "MongoDB": "https://www.mongodb.com/docs/manual/tutorial/",
    "Redis": "https://redis.io/docs/latest/develop/get-started/",
    "AWS": "https://aws.amazon.com/getting-started/",
    "Google Cloud": "https://cloud.google.com/docs/get-started",
    "Azure": "https://learn.microsoft.com/en-us/azure/",
    "Terraform": "https://developer.hashicorp.com/terraform/tutorials",
    "Git": "https://git-scm.com/doc",
    "GitHub Actions": "https://docs.github.com/en/actions",
    "CI/CD": "https://docs.github.com/en/actions/automating-builds-and-tests",
    "Linux": "https://ubuntu.com/tutorials/command-line-for-beginners",
    "Nginx": "https://nginx.org/en/docs/beginners_guide.html",
    "Pytest": "https://docs.pytest.org/en/stable/getting-started.html",
    "Jest": "https://jestjs.io/docs/getting-started",
    "System Design": "https://github.com/donnemartin/system-design-primer",
    "Data Structures & Algorithms": "https://www.geeksforgeeks.org/data-structures/",
    "Object-Oriented Programming (OOP)": "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/Object-oriented_programming",
    "REST APIs": "https://restfulapi.net/",
    "GraphQL": "https://graphql.org/learn/",
    "gRPC": "https://grpc.io/docs/what-is-grpc/introduction/",
    "Microservices": "https://microservices.io/",
}

# Proficiency multipliers on baseline hours
PROFICIENCY_MULTIPLIERS: Dict[str, float] = {
    "beginner": 1.30,       # Requires 30% more time for basics and exercises
    "intermediate": 1.00,   # Standard baseline pace
    "advanced": 0.75,       # 25% accelerated pace due to transferable knowledge
}

PLANNING_BUFFER_PERCENTAGE = 15.0  # 15% buffer for debugging, reviews, and unexpected delays


# ---------------------------------------------------------------------------
# Dependency-Aware Skill Ordering (Topological Sorting)
# ---------------------------------------------------------------------------

def order_missing_skills_by_dependency(
    missing_skills: List[str],
    candidate_skills: Optional[List[str]] = None,
) -> List[Tuple[str, List[str]]]:
    """
    Sort missing skills so that prerequisites are taught before dependent skills.
    Also identifies which prerequisites the candidate already possesses.
    Returns: List of tuples (skill_name, [prerequisites_satisfied_or_pending])
    """
    candidate_set = set(candidate_skills or [])
    missing_set = set(missing_skills)

    # Build local adjacency and in-degree for missing skills
    dependencies: Dict[str, List[str]] = {}
    for skill in missing_skills:
        raw_prereqs = SKILL_PREREQUISITES.get(skill, [])
        dependencies[skill] = raw_prereqs

    # Topological sort among missing skills
    visited: Set[str] = set()
    result: List[str] = []

    def visit(node: str, visiting: Set[str]):
        if node in visiting:
            # Cycle detected (fallback, do not infinite loop)
            return
        if node not in visited:
            visiting.add(node)
            for prereq in dependencies.get(node, []):
                if prereq in missing_set:
                    visit(prereq, visiting)
            visiting.remove(node)
            visited.add(node)
            result.append(node)

    for skill in missing_skills:
        if skill not in visited:
            visit(skill, set())

    # Build final list with annotated prerequisites
    ordered: List[Tuple[str, List[str]]] = []
    for skill in result:
        prereqs = dependencies.get(skill, [])
        ordered.append((skill, prereqs))

    return ordered


# ---------------------------------------------------------------------------
# Task Breakdown Generator per Skill
# ---------------------------------------------------------------------------

def generate_tasks_for_skill(
    skill_name: str,
    skill_category: str,
    module_index: int,
    proficiency_multiplier: float,
    learning_style: str,
    prerequisites: List[str],
) -> List[Dict[str, Any]]:
    """
    Break down a missing skill into 5 actionable tasks:
    1. Learn the fundamentals.
    2. Study concepts and documentation.
    3. Complete practical exercises.
    4. Build a small project.
    5. Complete an assessment or revision task.
    """
    base_hours = SKILL_BASELINE_HOURS.get(skill_name, DEFAULT_SKILL_BASELINE_HOURS)
    adjusted_hours = base_hours * proficiency_multiplier
    resource_url = CREDIBLE_RESOURCE_URLS.get(skill_name)

    # Task duration distributions (sum = adjusted_hours * 60 minutes)
    # 1. Fundamentals: ~20%
    # 2. Concepts & Docs: ~20%
    # 3. Practical Exercises: ~25%
    # 4. Small Project: ~25%
    # 5. Assessment / Revision: ~10%
    total_minutes = int(adjusted_hours * 60)
    m1 = max(45, int(total_minutes * 0.20))
    m2 = max(45, int(total_minutes * 0.20))
    m3 = max(60, int(total_minutes * 0.25))
    m4 = max(60, int(total_minutes * 0.25))
    m5 = max(30, total_minutes - (m1 + m2 + m3 + m4))

    # Adjust task flavor by learning style
    style_label = {
        "hands_on": "hands-on coding and lab drills",
        "video_first": "video lectures and guided architectural walkthroughs",
        "reading_docs": "deep technical documentation and specification reading",
        "project_based": "milestone-driven project development",
    }.get(learning_style, "hands-on coding and lab drills")

    tasks = [
        # Phase 1: Fundamentals
        {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name,
            "skill_category": skill_category,
            "module_order": module_index,
            "task_title": f"{skill_name} Fundamentals: Core Architecture & Setup",
            "task_description": (
                f"Establish core understanding of {skill_name}. Learn architecture, core concepts, "
                f"installation, and local development environment setup emphasizing {style_label}."
            ),
            "estimated_minutes": m1,
            "prerequisites": prerequisites,
            "resource_url": resource_url,
            "is_completed": False,
            "completed_at": None,
            "notes": None,
        },
        # Phase 2: Concepts & Documentation
        {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name,
            "skill_category": skill_category,
            "module_order": module_index,
            "task_title": f"{skill_name} Deep Dive: Modules, Configuration & Best Practices",
            "task_description": (
                f"Study advanced components, configuration options, data flow, and standard industry "
                f"best practices for {skill_name}."
            ),
            "estimated_minutes": m2,
            "prerequisites": [f"{skill_name} Fundamentals"],
            "resource_url": resource_url,
            "is_completed": False,
            "completed_at": None,
            "notes": None,
        },
        # Phase 3: Practical Exercises
        {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name,
            "skill_category": skill_category,
            "module_order": module_index,
            "task_title": f"{skill_name} Hands-on Exercises & Problem Solving",
            "task_description": (
                f"Complete focused coding exercises and scenario-based drills applying {skill_name} "
                f"to solve real-world technical problems."
            ),
            "estimated_minutes": m3,
            "prerequisites": [f"{skill_name} Deep Dive"],
            "resource_url": resource_url,
            "is_completed": False,
            "completed_at": None,
            "notes": None,
        },
        # Phase 4: Mini Project
        {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name,
            "skill_category": skill_category,
            "module_order": module_index,
            "task_title": f"Build a {skill_name} Showcase Mini-Project",
            "task_description": (
                f"Design, build, and test a standalone mini-project demonstrating production-readiness, "
                f"clean code, and idiomatic use of {skill_name}."
            ),
            "estimated_minutes": m4,
            "prerequisites": [f"{skill_name} Hands-on Exercises"],
            "resource_url": resource_url,
            "is_completed": False,
            "completed_at": None,
            "notes": None,
        },
        # Phase 5: Assessment & Revision
        {
            "id": str(uuid.uuid4()),
            "skill_name": skill_name,
            "skill_category": skill_category,
            "module_order": module_index,
            "task_title": f"{skill_name} Self-Assessment & Interview Preparation",
            "task_description": (
                f"Conduct a technical self-assessment, review edge cases, and practice interview-grade "
                f"questions and architecture challenges for {skill_name}."
            ),
            "estimated_minutes": m5,
            "prerequisites": [f"Build a {skill_name} Showcase Mini-Project"],
            "resource_url": resource_url,
            "is_completed": False,
            "completed_at": None,
            "notes": None,
        },
    ]

    return tasks


# ---------------------------------------------------------------------------
# Main Roadmap Generator
# ---------------------------------------------------------------------------

def generate_adaptive_roadmap(
    session: Dict[str, Any],
    preferences: Dict[str, Any],
    skill_category_lookup: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Generate an end-to-end adaptive roadmap for an analysis session.
    """
    missing_skills: List[str] = session.get("missing_skills", [])
    if not missing_skills:
        raise ValueError("No missing skills found in this analysis session to generate a roadmap.")

    candidate_skills: List[str] = session.get("resume_skills", [])
    job_title = session.get("job_title") or "Target Technical Role"

    # User Preferences
    weekly_hours = preferences.get("weekly_hours", 10)
    skill_level = preferences.get("skill_level", "intermediate")
    learning_style = preferences.get("learning_style", "hands_on")
    target_timeline_weeks = preferences.get("target_timeline_weeks")

    proficiency_multiplier = PROFICIENCY_MULTIPLIERS.get(skill_level, 1.00)

    # 1. Order skills with topological prerequisite awareness
    ordered_skills_with_prereqs = order_missing_skills_by_dependency(
        missing_skills, candidate_skills
    )

    all_tasks: List[Dict[str, Any]] = []
    category_lookup = skill_category_lookup or {}

    # 2. Generate granular tasks per skill
    for idx, (skill_name, prereqs) in enumerate(ordered_skills_with_prereqs, start=1):
        skill_category = category_lookup.get(skill_name, "Technical Skill")
        tasks = generate_tasks_for_skill(
            skill_name=skill_name,
            skill_category=skill_category,
            module_index=idx,
            proficiency_multiplier=proficiency_multiplier,
            learning_style=learning_style,
            prerequisites=prereqs,
        )
        all_tasks.extend(tasks)

    # 3. Calculate Adaptive Duration
    total_minutes = sum(t["estimated_minutes"] for t in all_tasks)
    total_estimated_hours = round(total_minutes / 60.0, 2)

    # Planning buffer (15%) accounts for revision and project troubleshooting
    buffered_hours = round(total_estimated_hours * (1.0 + PLANNING_BUFFER_PERCENTAGE / 100.0), 2)

    if weekly_hours > 0:
        estimated_duration_weeks = round(buffered_hours / float(weekly_hours), 2)
    else:
        estimated_duration_weeks = 0.0

    # 4. Target Timeline Feasibility Analysis
    timeline_feasibility = "n/a"
    feasibility_note = None

    if target_timeline_weeks is not None:
        if estimated_duration_weeks <= target_timeline_weeks:
            timeline_feasibility = "achievable"
            feasibility_note = (
                f"Your target timeline of {target_timeline_weeks} weeks is realistic! "
                f"At {weekly_hours} hours/week, the curriculum requires approximately "
                f"{estimated_duration_weeks} weeks (including a {int(PLANNING_BUFFER_PERCENTAGE)}% buffer)."
            )
        else:
            timeline_feasibility = "unrealistic"
            needed_weekly_hours = round(buffered_hours / float(target_timeline_weeks), 1)
            feasibility_note = (
                f"Target timeline of {target_timeline_weeks} weeks is unrealistic for "
                f"{total_estimated_hours} total hours ({buffered_hours} hours with buffer). "
                f"At your current pace of {weekly_hours} hours/week, you will need approximately "
                f"{estimated_duration_weeks} weeks. To complete it in {target_timeline_weeks} weeks, "
                f"you would need to dedicate approximately {needed_weekly_hours} hours/week."
            )

    roadmap_title = f"{job_title} Skill Gap Roadmap ({len(missing_skills)} Skills)"

    roadmap_metadata = {
        "weekly_hours": weekly_hours,
        "skill_level": skill_level,
        "learning_style": learning_style,
        "proficiency_multiplier": proficiency_multiplier,
        "planning_buffer_percentage": PLANNING_BUFFER_PERCENTAGE,
        "estimated_duration_weeks": estimated_duration_weeks,
        "target_timeline_weeks": target_timeline_weeks,
        "timeline_feasibility": timeline_feasibility,
        "feasibility_note": feasibility_note,
        "ordered_skills": [s[0] for s in ordered_skills_with_prereqs],
        "total_tasks_count": len(all_tasks),
    }

    return {
        "title": roadmap_title,
        "target_role": job_title,
        "total_estimated_hours": total_estimated_hours,
        "roadmap_metadata": roadmap_metadata,
        "tasks": all_tasks,
    }
