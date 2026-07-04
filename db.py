import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="Career_dashboard",
        user="postgres",
        password="0000"
    )

    return conn