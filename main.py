from fastapi import FastAPI
import requests
import psycopg2
import os
app = FastAPI()

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(database_url, sslmode="require")

@app.get("/")
def home():
    return {"Hello": "World"}


@app.get("/db-test")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"database_status": "connected", "result": result}
    except Exception as e:
        return {"error": str(e)}


@app.get("/test")
def test_params(owner: str, repo: str):
    return {
        "owner_received": owner,
        "repo_received": repo
    }

@app.get("/commits")
def get_commits(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Repository not found or API failed"}

    data = response.json()

    conn = get_db_connection()
    cursor = conn.cursor()

    inserted_count = 0

    for commit in data[:5]:
        author = commit["commit"]["author"]["name"]
        message = commit["commit"]["message"]
        date = commit["commit"]["author"]["date"]

        sha = commit["sha"]

        cursor.execute(
            """
            INSERT INTO commits (sha, repo_owner, repo_name, author, message, commit_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (sha) DO NOTHING
            RETURNING id;
            """,
            (sha, owner, repo, author, message, date)
        )

        if cursor.fetchone():
            inserted_count += 1
    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "stored in database", "inserted": inserted_count}

@app.get("/top-contributors")
def top_contributors(owner: str, repo: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT author, COUNT(*) as commit_count
            FROM commits
            WHERE repo_owner = %s AND repo_name = %s
            GROUP BY author
            ORDER BY commit_count DESC;
        """, (owner, repo))

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        contributors = [
            {"author": row[0], "commits": row[1]}
            for row in results
        ]

        return {"top_contributors": contributors}

    except Exception as e:
        return {"error": str(e)}

@app.get("/commit-activity")
def commit_activity(owner: str, repo: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DATE(commit_date) as commit_day, COUNT(*) as commit_count
            FROM commits
            WHERE repo_owner = %s AND repo_name = %s
            GROUP BY commit_day
            ORDER BY commit_day;
        """, (owner, repo))

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        activity = [
            {"date": str(row[0]), "commits": row[1]}
            for row in results
        ]

        return {"commit_activity": activity}

    except Exception as e:
        return {"error": str(e)}
@app.get("/repo-summary")
def repo_summary(owner: str, repo: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total_commits,
                COUNT(DISTINCT author) as total_contributors,
                MIN(commit_date) as first_commit,
                MAX(commit_date) as latest_commit
            FROM commits
            WHERE repo_owner = %s AND repo_name = %s;
        """, (owner, repo))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "total_commits": result[0],
            "total_contributors": result[1],
            "first_commit": str(result[2]) if result[2] else None,
            "latest_commit": str(result[3]) if result[3] else None
        }

    except Exception as e:
        return {"error": str(e)}
from fastapi import FastAPI
import psycopg2
import os

@app.on_event("startup")
def create_table():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commits (
            id SERIAL PRIMARY KEY,
            repo_owner TEXT,
            repo_name TEXT,
            sha TEXT UNIQUE,
            author TEXT,
            message TEXT,
            date TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()