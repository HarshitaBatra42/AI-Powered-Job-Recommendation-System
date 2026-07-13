import pandas as pd
import re

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    cosine_similarity = None

import google.generativeai as genai
from skills_utils import extract_skills, get_missing_skills
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# -----------------------------
# LOAD DATASET
# -----------------------------
jobs_data = pd.read_csv("job_title_des.csv")
jobs_data = jobs_data.head(200)  # keep small sample for performance
jobs_data = jobs_data.dropna(subset=["Job Description", "Job Title"])
jobs_data = jobs_data.reset_index(drop=True)

embedding_model = None
if SentenceTransformer is not None:
    try:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        embedding_model = None

# -----------------------------
# PRECOMPUTE JOB EMBEDDINGS ONCE (fixes major perf bug)
# -----------------------------
# Previously this ran inside recommend_jobs() on every single call, re-embedding
# all 200 job descriptions per request even though they never change.
# Now it runs once, when the module is first imported (app startup / first request
# on Streamlit Cloud), and is reused for every subsequent recommendation.
job_embeddings = None
if embedding_model is not None:
    try:
        _job_descriptions = jobs_data["Job Description"].astype(str).tolist()
        job_embeddings = embedding_model.encode(_job_descriptions)
    except Exception:
        job_embeddings = None

# -----------------------------
# SKILL LIST (Sorted by length for proper matching)
# -----------------------------
SKILLS = [
    # Multi-word skills first (longest match priority)
    "business intelligence", "prompt engineering", "machine learning",
    "data visualization", "business analysis", "penetration testing",
    "shell scripting", "product analytics", "data modeling",
    "power query", "deep learning", "data science", "kali linux",
    "power bi", "ab testing",
    # Libraries & Frameworks
    "tensorflow", "pytorch", "pandas", "numpy", "opencv", "spark",
    "hadoop", "django", "react",
    # Databases
    "mysql", "mongodb", "oracle", "sql",
    # Languages
    "python", "javascript", "java", "c", "html", "css",
    # BI / Analytics
    "excel", "tableau", "dashboard", "reporting", "etl", "dax",
    # Cloud / DevOps
    "docker", "kubernetes", "aws", "cloud",
    # Security
    "cybersecurity", "networking", "wireshark", "security", "cisco",
    "routing", "switching", "monitoring",
    # Misc
    "nodejs", "selenium", "testng", "linux", "nlp", "llm",
    "matplotlib", "scikit-learn", "sklearn", "github", "git",
    "seaborn", "flask", "fastapi", "streamlit"
]

ROLE_SKILLS = {
    "junior data scientist": {"python", "sql", "machine learning", "numpy", "pandas", "scikit-learn", "matplotlib", "seaborn"},
    "data scientist": {"python", "sql", "machine learning", "numpy", "pandas", "scikit-learn", "tensorflow", "matplotlib", "seaborn"},
    "data analyst": {"sql", "excel", "power bi", "tableau", "python", "pandas"},
    "business analyst": {"sql", "excel", "power bi", "tableau"},
    "product analyst": {"sql", "python", "excel", "power bi", "ab testing"}
}

SINGLE_LETTER_SKILLS = {
    "c": r"(?<![a-z])\bc(?![a-z#+])",
    "r": r"(?<![a-z])\br(?![a-z])",
}

SKILL_ALIASES = {
    "ml": "machine learning",
    "ai": "machine learning",
    "db": "database",
    "nlp": "nlp",
    "llm": "llm",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tf": "tensorflow",
    "js": "javascript",
}


def normalize_skill(skill):
    """Normalize skill names and handle aliases"""
    skill = skill.lower().strip()
    return SKILL_ALIASES.get(skill, skill)


SKILL_WEIGHTS = {
    "data scientist": {"python": 5, "machine learning": 5, "tensorflow": 5, "pandas": 4, "sql": 4, "matplotlib": 3, "power bi": 2, "excel": 2},
    "junior data scientist": {"python": 5, "machine learning": 5, "tensorflow": 5, "pandas": 4, "sql": 4, "matplotlib": 3, "power bi": 2, "excel": 2},
    "data analyst": {"sql": 5, "power bi": 5, "excel": 5, "python": 3, "pandas": 3, "matplotlib": 2},
    "business analyst": {"sql": 5, "excel": 5, "power bi": 4, "python": 2},
    "product analyst": {"sql": 5, "python": 4, "pandas": 4, "machine learning": 3, "power bi": 2},
    "analytics engineer": {"sql": 5, "python": 4, "data modeling": 5, "power bi": 3}
}

CRITICAL_SKILLS = {
    "data scientist": ["python", "machine learning", "sql"],
    "junior data scientist": ["python", "machine learning", "sql"],
    "data analyst": ["sql", "excel"],
    "product analyst": ["python", "sql"],
    "business analyst": ["sql", "excel"]
}


def detect_resume_category(skills):
    skills = set([s.lower() for s in skills])
    if "machine learning" in skills or "deep learning" in skills or "tensorflow" in skills or "pytorch" in skills:
        return "ml"
    elif "sql" in skills or "pandas" in skills or "data science" in skills:
        return "data"
    elif "react" in skills or "django" in skills or "javascript" in skills:
        return "developer"
    elif "cybersecurity" in skills or "kali linux" in skills or "wireshark" in skills:
        return "cyber"
    elif "aws" in skills or "docker" in skills or "kubernetes" in skills:
        return "cloud"
    return "general"


# -----------------------------
# SKILL EXTRACTION
# -----------------------------
def extract_job_skills(text):
    text = str(text).lower()
    detected = set()

    for alias, actual in SKILL_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            detected.add(actual)

    sorted_skills = sorted(SKILLS, key=len, reverse=True)
    for skill in sorted_skills:
        if skill in detected:
            continue
        if len(skill) == 1 and skill not in SINGLE_LETTER_SKILLS:
            continue
        if skill in SINGLE_LETTER_SKILLS:
            pattern = SINGLE_LETTER_SKILLS[skill]
        elif skill == "c#":
            pattern = r"\bc#\b"
        elif skill == "c++":
            pattern = r"\bc\+\+\b"
        elif "/" in skill or "-" in skill:
            pattern = re.escape(skill)
        else:
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text):
            detected.add(skill)

    return sorted(detected)


def categorize_missing_skills(missing_skills):
    """Categorize missing skills by priority (data-driven)"""
    high_priority_skills = {"python", "sql", "tensorflow", "pytorch", "machine learning", "deep learning", "pandas", "numpy"}
    medium_priority_skills = {"llm", "prompt engineering", "aws", "docker", "power bi", "tableau", "excel", "javascript"}

    high, medium, low = [], [], []
    for skill in missing_skills:
        skill_norm = skill.lower().strip()
        if skill_norm in high_priority_skills:
            high.append(skill_norm)
        elif skill_norm in medium_priority_skills:
            medium.append(skill_norm)
        else:
            low.append(skill_norm)

    return {"high": high, "medium": medium, "low": low}


def generate_resume_suggestions_gemini(top_job, skills, missing_skills, ats_data):
    prompt = f"""
You are an expert Resume Mentor.

Target Job:
{top_job}

Current Skills:
{skills}

Missing Skills:
{missing_skills}

ATS Breakdown:
Skills Score: {ats_data['skills_score']}/40
Projects Score: {ats_data['projects_score']}/25
Education Score: {ats_data['education_score']}/15
Certifications Score: {ats_data['certifications_score']}/10
Links Score: {ats_data['links_score']}/10

Give exactly 5 resume improvement suggestions.
Rules:
- One line each
- Practical suggestions
- Focus on improving resume and job readiness
- Do not write paragraphs
"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text


JOB_CATEGORIES = {
    "Data Scientist": "data", "Junior Data Scientist": "data", "Data Analyst": "data",
    "Business Analyst": "data", "Product Analyst": "data", "ML Engineer": "ml",
    "AI Engineer": "ml", "Backend Developer": "developer", "Frontend Developer": "developer",
    "Full Stack Developer": "developer", "Cyber Security Analyst": "cyber",
    "SOC Analyst": "cyber", "Cloud Engineer": "cloud", "DevOps Engineer": "devops",
    "Power BI Developer": "bi", "BI Developer": "bi"
}


# -----------------------------
# MAIN RECOMMENDER
# -----------------------------
def recommend_jobs(user_resume_text):
    if embedding_model is None or cosine_similarity is None or job_embeddings is None:
        return [
            {
                "Job Title": "Resume Analysis Unavailable",
                "skill_score": 0.0,
                "resume_score": 0.0,
                "overall_score": 0.0,
                "missing_skills": ["Install sentence-transformers and scikit-learn to enable job recommendations."],
            }
        ]

    user_resume_text = str(user_resume_text)
    user_skills = {normalize_skill(skill) for skill in extract_skills(user_resume_text)}
    resume_category = detect_resume_category(user_skills)

    results = jobs_data.copy().reset_index(drop=True)

    # FIX: reuse the precomputed job_embeddings instead of re-encoding all jobs
    # every time a user submits a resume. Only the resume itself needs embedding now.
    resume_embedding = embedding_model.encode([user_resume_text])
    similarities = cosine_similarity(resume_embedding, job_embeddings)[0]

    skill_scores, resume_scores, overall_scores = [], [], []

    for i, desc in enumerate(results["Job Description"]):
        job_skills = {normalize_skill(skill) for skill in extract_job_skills(desc)}
        job_title = str(results.iloc[i]["Job Title"]).lower()

        for role, skills in ROLE_SKILLS.items():
            if role in job_title:
                job_skills.update(normalize_skill(skill) for skill in skills)
                break

        if len(job_skills) == 0:
            skill_score = 0
        else:
            weights = {}
            for role, role_weights in SKILL_WEIGHTS.items():
                if role in job_title:
                    weights = {normalize_skill(skill): weight for skill, weight in role_weights.items()}
                    break

            total_weight = 0
            matched_weight = 0
            for skill in job_skills:
                weight = weights.get(skill, 1)
                total_weight += weight
                if skill in user_skills:
                    matched_weight += weight
            skill_score = 0 if total_weight == 0 else (matched_weight / total_weight) * 100

        embedding_score = similarities[i] * 100
        final_score = 0.4 * embedding_score + 0.6 * skill_score

        lower_resume = user_resume_text.lower()
        if "machine learning" in lower_resume and "data scientist" in job_title:
            final_score += 10
        if "machine learning" in lower_resume and "analyst" in job_title:
            final_score -= 5

        for role, required_skills in CRITICAL_SKILLS.items():
            if role in job_title:
                missing_count = sum(1 for skill in required_skills if normalize_skill(skill) not in user_skills)
                final_score -= missing_count * 10
                break

        final_score = max(final_score, 0)

        skill_scores.append(round(skill_score, 2))
        resume_scores.append(round(embedding_score, 2))
        overall_scores.append(round(final_score, 2))

    results["skill_score"] = skill_scores
    results["resume_score"] = resume_scores
    results["overall_score"] = overall_scores

    results = results.sort_values(by="overall_score", ascending=False)
    results = results.drop_duplicates(subset=["Job Title"]).reset_index(drop=True)

    missing_list = []
    for _, row in results.iterrows():
        job_title = str(row["Job Title"]).lower()
        job_description = str(row["Job Description"])
        missing_skills = get_missing_skills(
            job_title, job_description, user_skills,
            role_skills=ROLE_SKILLS, critical_skills=CRITICAL_SKILLS,
            skill_weights=SKILL_WEIGHTS, limit=6,
        )
        missing_list.append(missing_skills)

    results["missing_skills"] = missing_list
    results = results.fillna("")

    return results.to_dict(orient="records")


def generate_interview_questions(job_title, skills, missing_skills, num_questions=10):
    skills_text = ", ".join(skills) if skills else "general foundational skills"
    missing_text = ", ".join(missing_skills) if missing_skills else "none identified"

    prompt = f"""
You are an experienced technical interviewer preparing a candidate for a {job_title} interview.

Candidate's current skills: {skills_text}
Candidate's missing/weak skills for this role: {missing_text}

Generate exactly {num_questions} interview questions for this candidate, mixing:
- Technical questions based on their CURRENT skills (to test real depth, not just definitions)
- A few technical questions specifically targeting their MISSING skills (so they can prepare for likely gaps)
- Behavioral/HR questions appropriate for this role level

Format each line EXACTLY like this, one question per line, no numbering, no extra text:
Technical: <question>
Behavioral: <question>

Do not add any introduction, explanation, or summary. Only output the {num_questions} lines, nothing else.
"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    questions = []
    for line in raw_text.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        category, question_text = line.split(":", 1)
        category = category.strip().lower()
        question_text = question_text.strip()
        if category not in ["technical", "behavioral"]:
            category = "technical"
        if question_text:
            questions.append({"category": category, "question": question_text})

    return questions


def generate_ai_insights(resume_text, job_title, skills, missing_skills):
    prompt = f"""
You are an AI Career Assistant.

Resume Skills:
{skills}

Target Job:
{job_title}

Missing Skills:
{missing_skills}

Give:
1. ATS Feedback (1-2 lines)
2. Why this job fits / not fits
3. Learning roadmap (3 steps only)
4. 2 project ideas

Be short and structured.
"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text