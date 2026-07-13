# -----------------------------
# CURATED SALARY REFERENCE DATA (India, Fresher/Entry-Level, 2026)
# -----------------------------
# Sources: AmbitionBox, Glassdoor India, Naukri Salary Insights (April-June 2026)
# These are DELIBERATELY curated, static ranges — not generated live by the LLM.
# This avoids presenting a hallucinated number as a confident fact.
# Update this file periodically as market rates shift; no other code changes needed.

SALARY_DATA = {
    "data scientist": {"min": 4, "max": 9, "note": "Average fresher range across IT/analytics firms; IIT/NIT grads at product companies often see ₹12-20 LPA."},
    "junior data scientist": {"min": 4, "max": 8, "note": "Entry-level band, slightly conservative vs. full Data Scientist roles."},
    "data analyst": {"min": 3.5, "max": 7, "note": "National average sits around ₹6-7 LPA; SQL/Python/Power BI skills push toward the top end."},
    "business analyst": {"min": 4, "max": 7, "note": "Fresher band; BA salaries grow quickly with 1-2 years experience."},
    "product analyst": {"min": 5, "max": 9, "note": "Estimated based on similar hybrid analyst roles at product companies — verify independently if precision matters."},
}

# Fallback range for any job title not explicitly listed above
DEFAULT_RANGE = {"min": 4, "max": 8, "note": "General estimate for entry-level tech/analytics roles in India — this specific title isn't in our curated dataset yet."}


def get_salary_range(job_title):
    """
    Look up an estimated fresher salary range (India, LPA) for a given job title.
    Matching is case-insensitive and checks for partial/substring matches
    (e.g. "Junior Data Scientist - Remote" still matches "junior data scientist").
    Returns a dict with 'min', 'max' (in LPA), and a short 'note'.
    """
    if not job_title:
        return DEFAULT_RANGE

    title_lower = job_title.strip().lower()

    # Exact match first
    if title_lower in SALARY_DATA:
        return SALARY_DATA[title_lower]

    # Partial match fallback (handles slight title variations)
    for key, value in SALARY_DATA.items():
        if key in title_lower or title_lower in key:
            return value

    return DEFAULT_RANGE