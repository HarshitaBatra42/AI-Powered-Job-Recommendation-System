from skills_utils import get_missing_skills


def test_missing_skills_are_richer_for_data_roles():
    missing = get_missing_skills(
        "Data Scientist",
        "Experience with Python, SQL, and dashboards.",
        ["python", "sql", "tableau"],
        limit=6,
    )

    assert "machine learning" in missing
    assert "pandas" in missing
    assert "numpy" in missing
