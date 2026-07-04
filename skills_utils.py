import re

SKILL_DB = [
    # Languages
    "python", "java", "c", "c++", "c#", "javascript",
    "typescript", "go", "rust",

    # Database
    "sql", "mysql", "postgresql", "mongodb",
    "oracle", "sqlite",

    # Data Science
    "numpy", "pandas", "matplotlib",
    "seaborn", "scikit-learn",
    "machine learning", "deep learning",
    "tensorflow", "pytorch",
    "opencv", "nlp",

    # Web
    "html", "css", "react", "nodejs",
    "django", "flask", "fastapi",

    # Cloud
    "aws", "azure", "gcp",
    "docker", "kubernetes",

    # Analytics
    "power bi", "tableau", "excel",

    # AI
    "llm", "langchain",
    "prompt engineering",
    "huggingface",

    # DevOps
    "jenkins", "github actions",

    # Cyber
    "wireshark", "kali linux",
    "penetration testing",
    "cybersecurity",
    "networking",

    # Tools
    "git", "github", "linux"
]

SKILL_ALIASES = {
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "powerbi": "power bi",
    "tf": "tensorflow",
    "js": "javascript",
    "ml": "machine learning",
    "dl": "deep learning"
}

DEFAULT_ROLE_SKILLS = {
    "data scientist": {
        "python", "sql", "machine learning", "numpy", "pandas",
        "scikit-learn", "tensorflow", "matplotlib", "seaborn"
    },
    "junior data scientist": {
        "python", "sql", "machine learning", "numpy", "pandas",
        "scikit-learn", "matplotlib", "seaborn"
    },
    "data analyst": {
        "sql", "excel", "power bi", "tableau", "python", "pandas"
    },
    "business analyst": {
        "sql", "excel", "power bi", "tableau"
    },
    "product analyst": {
        "sql", "python", "excel", "power bi", "ab testing"
    }
}

DEFAULT_CRITICAL_SKILLS = {
    "data scientist": ["python", "machine learning", "sql"],
    "junior data scientist": ["python", "machine learning", "sql"],
    "data analyst": ["sql", "excel"],
    "business analyst": ["sql", "excel"],
    "product analyst": ["python", "sql"]
}


def normalize_skill_name(skill):
    if skill is None:
        return ""
    text = str(skill).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return SKILL_ALIASES.get(text, text)


def get_missing_skills(job_title, job_description, resume_skills, role_skills=None, critical_skills=None, skill_weights=None, limit=6):
    if resume_skills is None:
        resume_skills = []

    if isinstance(resume_skills, (set, list, tuple)):
        resume_skill_set = {normalize_skill_name(skill) for skill in resume_skills if skill}
    else:
        resume_skill_set = {normalize_skill_name(skill) for skill in extract_skills(str(resume_skills))}

    normalized_title = normalize_skill_name(job_title or "")
    description_text = str(job_description or "")

    candidate_scores = {}

    for skill in extract_skills(description_text):
        candidate_scores[normalize_skill_name(skill)] = candidate_scores.get(normalize_skill_name(skill), 0) + 2

    chosen_role_skills = role_skills or DEFAULT_ROLE_SKILLS
    chosen_critical_skills = critical_skills or DEFAULT_CRITICAL_SKILLS
    chosen_weights = skill_weights or {}

    for role, skills in chosen_role_skills.items():
        if role in normalized_title:
            for skill in skills:
                skill_name = normalize_skill_name(skill)
                candidate_scores[skill_name] = max(candidate_scores.get(skill_name, 0), 5)
            break

    for role, skills in chosen_critical_skills.items():
        if role in normalized_title:
            for skill in skills:
                skill_name = normalize_skill_name(skill)
                candidate_scores[skill_name] = max(candidate_scores.get(skill_name, 0), 9)
            break

    for role, weights in chosen_weights.items():
        if role in normalized_title:
            for skill, weight in weights.items():
                skill_name = normalize_skill_name(skill)
                candidate_scores[skill_name] = max(candidate_scores.get(skill_name, 0), 6 + int(weight))
            break

    missing = []
    for skill, score in sorted(candidate_scores.items(), key=lambda item: (-item[1], item[0])):
        if skill and skill not in resume_skill_set:
            missing.append(skill)
            if len(missing) >= limit:
                break

    if len(missing) < 2:
        for role, skills in chosen_role_skills.items():
            if role in normalized_title:
                for skill in skills:
                    skill_name = normalize_skill_name(skill)
                    if skill_name not in resume_skill_set and skill_name not in missing:
                        missing.append(skill_name)
                        if len(missing) >= limit:
                            break
                break

    if len(missing) == 0:
        missing = ["advanced analytics", "statistical modeling"]

    return missing


def extract_skills(text):
    if text is None:
        return []

    text = str(text).lower()
    found = set()

    for alias, actual in SKILL_ALIASES.items():
        if alias in text:
            found.add(actual)

    if re.search(r"\bc\+\+\b", text):
        found.add("c++")

    if re.search(r"\bc#\b", text):
        found.add("c#")

    if re.search(r"(?<!\+)?\bc\b(?!\+)", text):
        found.add("c")

    for skill in SKILL_DB:
        if skill in {"c", "c++", "c#"}:
            continue

        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found.add(skill)

    return sorted(found)
