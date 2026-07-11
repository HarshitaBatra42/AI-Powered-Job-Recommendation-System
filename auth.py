import bcrypt
from db import get_connection


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage. Returns a UTF-8 string safe for a VARCHAR/TEXT column."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_user(name, email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cur.execute(
            """
            INSERT INTO users(name, email, password)
            VALUES (%s, %s, %s)
            """,
            (name, email, hashed_pw)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, password
            FROM users
            WHERE email = %s
            """,
            (email,)
        )
        user = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if user is None:
        return None  # no such email

    user_id, name, stored_hash = user
    if verify_password(password, stored_hash):
        return (user_id, name)  # same shape as before: (id, name)
    return None  # wrong password


def save_report(user_id, resume_name, ats_score, top_job):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO reports (user_id, resume_name, ats_score, top_job)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, resume_name, ats_score, top_job)
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_reports(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT resume_name, ats_score, top_job, created_at
            FROM reports
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        reports = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return reports