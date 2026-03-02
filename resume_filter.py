from typing import Any


resume_data: dict[str, Any] = {
    "skills": [
        "Python",
        "Django",
        "Flask",
        "FastAPI",
        "LangChain",
        "LLM",
        "SQL",
        "PostgreSQL",
        "MongoDB",
        "Docker",
        "Git",
        "Linux",
        "AWS",
        "NLP",
        "RAG",
        "Machine Learning",
        "YOLO",
        "Azure Cloud",
        "REST API",
    ],
    "summary": (
        "Backend-focused AI developer experienced with Python, LLM applications, "
        "APIs, databases, and cloud-backed backend development."
    ),
}


def score_job_against_resume(
    description_text: str, candidate_resume: dict[str, Any] | None = None
) -> tuple[float, list[str]]:
    resume = candidate_resume or resume_data
    skills = [skill for skill in resume.get("skills", []) if isinstance(skill, str) and skill.strip()]
    if not skills:
        return 0.0, []

    lowered_description = description_text.lower()
    matched_skills = [skill for skill in skills if skill.lower() in lowered_description]
    score = len(matched_skills) / len(skills)

    return score, matched_skills
