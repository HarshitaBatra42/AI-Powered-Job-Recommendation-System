from db import get_connection


def create_user(name, email, password):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users(name,email,password)
        VALUES(%s,%s,%s)
        """,
        (name, email, password)
    )

    conn.commit()

    cur.close()
    conn.close()


def login_user(email, password):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id,name
        FROM users
        WHERE email=%s
        AND password=%s
        """,
        (email, password)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user

def save_report(
    user_id,
    resume_name,
    ats_score,
    top_job
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO reports
        (
            user_id,
            resume_name,
            ats_score,
            top_job
        )
        VALUES
        (%s,%s,%s,%s)
        """,
        (
            user_id,
            resume_name,
            ats_score,
            top_job
        )
    )

    conn.commit()

    cur.close()
    conn.close()


def get_reports(user_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
        resume_name,
        ats_score,
        top_job,
        created_at
        FROM reports
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    reports = cur.fetchall()

    cur.close()
    conn.close()

    return reports