from __future__ import annotations

from copy import deepcopy
from math import ceil
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError
from app.models import EducationProgram, SimulationScenario, University, User, UserRoadmap
from app.schemas import RoadmapPreviewRequest, WorkspacePreferences, WorkspaceProfile


DEFAULT_PROFILE = WorkspaceProfile().model_dump()
DEFAULT_PREFERENCES = WorkspacePreferences().model_dump()
DEFAULT_CONNECTIONS = {
    "youtube": {"connected": False, "available": True, "label": "Not connected"},
    "github": {"connected": False, "available": False, "label": "OAuth not configured"},
    "linkedin": {"connected": False, "available": False, "label": "OAuth not configured"},
}

COURSES = [
    {"id": "sql-fundamentals", "title": "SQL fundamentals", "description": "Learn the core concepts of SQL and practice with real-world data examples.", "level": "Beginner", "language": "English", "format": "Self-paced", "duration": "4–6 hours", "skills": ["SQL", "Databases"], "provider_name": "Fence learning catalog", "provider_url": None},
    {"id": "fastapi-zero", "title": "FastAPI from zero", "description": "Build practical APIs with validation, documentation and testing.", "level": "Beginner", "language": "English", "format": "Self-paced", "duration": "6–8 hours", "skills": ["FastAPI", "APIs", "Python"], "provider_name": "Fence learning catalog", "provider_url": None},
    {"id": "git-essentials", "title": "Git essentials", "description": "Master version control with Git and collaborate confidently on real projects.", "level": "Beginner", "language": "English", "format": "Self-paced", "duration": "3–5 hours", "skills": ["Git", "Version control"], "provider_name": "Fence learning catalog", "provider_url": None},
    {"id": "python-testing", "title": "Python testing", "description": "Write reliable automated tests and improve the quality of your projects.", "level": "Intermediate", "language": "English", "format": "Self-paced", "duration": "5–7 hours", "skills": ["Python", "Testing", "Pytest"], "provider_name": "Fence learning catalog", "provider_url": None},
]

ILLUSTRATIVE_UNIVERSITIES = [
    {"id": "sample-wsiiz", "name": "WSiiZ", "country": "Poland", "city": "Rzeszów", "website": "https://wsiz.edu.pl", "description": "Practice-oriented programmes with a strong focus on IT and management.", "annual_tuition": 6000.0, "currency": "EUR", "duration_years": 3.0, "study_mode": "Full-time", "program_name": "Computer Science", "data_quality": "illustrative"},
    {"id": "sample-uw", "name": "University of Warsaw", "country": "Poland", "city": "Warsaw", "website": "https://www.uw.edu.pl", "description": "Research-led education with a broad range of computer science programmes.", "annual_tuition": 4500.0, "currency": "EUR", "duration_years": 3.0, "study_mode": "Full-time", "program_name": "Computer Science", "data_quality": "illustrative"},
    {"id": "sample-agh", "name": "AGH University of Krakow", "country": "Poland", "city": "Kraków", "website": "https://www.agh.edu.pl", "description": "Technical education with strong industry partnerships.", "annual_tuition": 4000.0, "currency": "EUR", "duration_years": 3.0, "study_mode": "Full-time", "program_name": "Computer Science", "data_quality": "illustrative"},
    {"id": "sample-pwr", "name": "Wrocław University of Science and Technology", "country": "Poland", "city": "Wrocław", "website": "https://pwr.edu.pl", "description": "Technology programmes supported by modern facilities and applied research.", "annual_tuition": 4200.0, "currency": "EUR", "duration_years": 3.0, "study_mode": "Full-time", "program_name": "Computer Science", "data_quality": "illustrative"},
]


def _merged_workspace_data(user: User) -> dict[str, Any]:
    stored = user.workspace_data if isinstance(user.workspace_data, dict) else {}
    return {
        "profile": {**DEFAULT_PROFILE, **stored.get("profile", {})},
        "preferences": {**DEFAULT_PREFERENCES, **stored.get("preferences", {})},
        "connections": {**DEFAULT_CONNECTIONS, **stored.get("connections", {})},
        "saved_course_ids": list(stored.get("saved_course_ids", [])),
    }


def preview_roadmap(payload: RoadmapPreviewRequest) -> dict[str, Any]:
    level_factor = {"Beginner": 1.0, "Intermediate": 0.78, "Advanced": 0.58}[payload.current_level]
    skill_credit = min(len({skill.casefold() for skill in payload.skills}) * 8, 48)
    phase_blueprints = [
        ("foundations", "Foundations", 80, ["Python", "Data structures", "Problem solving"]),
        ("backend", "Backend development", 100, ["APIs", "FastAPI", "Databases", "SQL", "Testing"]),
        ("career", "Projects & career prep", 60, ["Project development", "Deployment", "Git workflow", "Technical interview prep"]),
    ]
    phases = []
    remaining_credit = skill_credit
    total_hours = 0
    for phase_id, title, base_hours, skills in phase_blueprints:
        adjusted = max(24, round(base_hours * level_factor) - min(remaining_credit, 16))
        remaining_credit = max(0, remaining_credit - 16)
        total_hours += adjusted
        phases.append({"id": phase_id, "title": title, "hours": adjusted, "weeks": ceil(adjusted / payload.hours_per_week), "skills": skills})
    return {"target_job": payload.target_job, "current_level": payload.current_level, "hours_per_week": payload.hours_per_week, "skills": payload.skills, "total_hours": total_hours, "weeks": ceil(total_hours / payload.hours_per_week), "phases": phases}


def build_local_roadmap(payload: RoadmapPreviewRequest, source: str = "local") -> dict[str, Any]:
    preview = preview_roadmap(payload)
    task_sets = {
        "foundations": [("python-fundamentals", "Python fundamentals", "Refresh core Python concepts"), ("git-version-control", "Git and version control", "Use Git for real projects")],
        "backend": [("fastapi-project", "Build a FastAPI project", "Create a real-world API with FastAPI"), ("sql-postgresql", "SQL and PostgreSQL", "Work with databases"), ("testing-quality", "Testing and quality", "Write tests and improve code quality"), ("deploy-project", "Deploy your project", "Deploy to the cloud")],
        "career": [("portfolio", "Create a portfolio", "Present your strongest projects"), ("interview-prep", "Prepare for interviews", "Practice technical and behavioural interviews")],
    }
    for phase in preview["phases"]:
        phase["tasks"] = [{"id": task_id, "title": title, "description": description, "completed": False} for task_id, title, description in task_sets[phase["id"]]]
    return {"source": source, "normalized": preview, "target_job": payload.target_job}


def normalize_roadmap(data: dict[str, Any], target_job: str) -> dict[str, Any]:
    normalized = data.get("normalized") if isinstance(data, dict) else None
    if isinstance(normalized, dict) and isinstance(normalized.get("phases"), list):
        return normalized
    payload = RoadmapPreviewRequest(target_job=target_job, hours_per_week=8, skills=[])
    return build_local_roadmap(payload, source="normalized_fallback")["normalized"]


class WorkspaceService:
    def __init__(self, session: Session):
        self.session = session

    def state_for_user(self, user: User) -> dict[str, Any]:
        state = _merged_workspace_data(user)
        scenarios = self.session.scalar(select(func.count()).select_from(SimulationScenario).where(SimulationScenario.user_id == user.id)) or 0
        roadmap = self.session.execute(select(UserRoadmap).where(UserRoadmap.user_id == user.id).order_by(desc(UserRoadmap.updated_at))).scalars().first()
        roadmap_data = None
        if roadmap:
            roadmap_data = {"id": roadmap.id, "target_job": roadmap.target_job, "updated_at": roadmap.updated_at.isoformat(), "plan": normalize_roadmap(roadmap.roadmap_data, roadmap.target_job)}
        return {"user": {"id": user.id, "username": user.username, "email": user.email, "plan": user.plan, "scenario_count": scenarios}, **state, "roadmap": roadmap_data}

    def update_profile(self, user: User, username: str | None, profile: WorkspaceProfile) -> dict[str, Any]:
        if username:
            existing = self.session.execute(select(User.id).where(func.lower(User.username) == username.casefold(), User.id != user.id)).scalar_one_or_none()
            if existing is not None:
                raise AppError("Це ім'я користувача вже зайняте", status_code=409)
            user.username = username
        state = _merged_workspace_data(user)
        state["profile"] = profile.model_dump()
        user.workspace_data = state
        self.session.commit()
        return self.state_for_user(user)

    def update_preferences(self, user: User, preferences: WorkspacePreferences) -> dict[str, Any]:
        state = _merged_workspace_data(user)
        state["preferences"] = preferences.model_dump()
        user.workspace_data = state
        self.session.commit()
        return self.state_for_user(user)

    def courses(self, user: User, query: str = "", level: str = "", language: str = "", course_format: str = "") -> list[dict[str, Any]]:
        saved = set(_merged_workspace_data(user)["saved_course_ids"])
        normalized_query = query.strip().casefold()
        results = []
        for course in COURSES:
            haystack = " ".join([course["title"], course["description"], *course["skills"]]).casefold()
            if normalized_query and normalized_query not in haystack:
                continue
            if level and level != "All levels" and course["level"] != level:
                continue
            if language and language != "All languages" and course["language"] != language:
                continue
            if course_format and course_format != "Any" and course["format"] != course_format:
                continue
            results.append({**course, "saved": course["id"] in saved})
        return results

    def set_course_saved(self, user: User, course_id: str, saved: bool) -> dict[str, Any]:
        if course_id not in {course["id"] for course in COURSES}:
            raise AppError("Курс не знайдено", status_code=404)
        state = _merged_workspace_data(user)
        course_ids = set(state["saved_course_ids"])
        course_ids.add(course_id) if saved else course_ids.discard(course_id)
        state["saved_course_ids"] = sorted(course_ids)
        user.workspace_data = state
        self.session.commit()
        return next({**course, "saved": saved} for course in COURSES if course["id"] == course_id)

    def universities(self, country: str, faculty: str, query: str) -> list[dict[str, Any]]:
        statement = select(University).options(selectinload(University.programs))
        if country:
            statement = statement.where(func.lower(University.country) == country.casefold())
        if query:
            statement = statement.where(University.name.ilike(f"%{query}%"))
        rows = self.session.execute(statement.order_by(University.name).limit(20)).scalars().unique().all()
        results = []
        for university in rows:
            programs = university.programs
            if faculty:
                matches = [program for program in programs if faculty.casefold() in program.name.casefold()]
                programs = matches or programs
            program: EducationProgram | None = programs[0] if programs else None
            results.append({"id": f"db-{university.id}", "name": university.name, "country": university.country, "city": None, "website": university.website, "description": program.description if program and program.description else "University programme stored in the Fence data catalog.", "annual_tuition": float(program.tuition_cost) if program else None, "currency": "USD", "duration_years": float(program.duration_years) if program else None, "study_mode": "Full-time", "program_name": program.name if program else faculty or "Programme not selected", "data_quality": "database"})
        if results:
            return results
        return [item for item in ILLUSTRATIVE_UNIVERSITIES if (not country or item["country"].casefold() == country.casefold()) and (not query or query.casefold() in item["name"].casefold())]

    def update_roadmap_task(self, user: User, roadmap_id: int, task_id: str, completed: bool) -> dict[str, Any]:
        roadmap = self.session.execute(select(UserRoadmap).where(UserRoadmap.id == roadmap_id, UserRoadmap.user_id == user.id)).scalar_one_or_none()
        if roadmap is None:
            raise AppError("Roadmap не знайдено", status_code=404)
        data = deepcopy(roadmap.roadmap_data)
        normalized = normalize_roadmap(data, roadmap.target_job)
        found = False
        for phase in normalized.get("phases", []):
            for task in phase.get("tasks", []):
                if task.get("id") == task_id:
                    task["completed"] = completed
                    found = True
        if not found:
            raise AppError("Завдання roadmap не знайдено", status_code=404)
        data["normalized"] = normalized
        roadmap.roadmap_data = data
        self.session.commit()
        return {"id": roadmap.id, "target_job": roadmap.target_job, "plan": normalized}
