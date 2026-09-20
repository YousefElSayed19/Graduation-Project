"""
vulnerable_target/app.py
--------------------------
A small test site with 5 intentional vulnerabilities, one per scanner,
so you can test the tool safely without touching a real website.

Runs on a separate port (5001) from the dashboard (5000):
    python vulnerable_target/app.py

Warning: this code is intentionally insecure (educational only).
Never use these patterns in a real project.
"""

import sqlite3
from flask import Flask, request, g

app = Flask(__name__)
DB_PATH = "vulnerable_target/test.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
    return db


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            email TEXT,
            secret_note TEXT
        )
    """)
    conn.execute("DELETE FROM users")
    conn.executemany(
        "INSERT INTO users (id, username, email, secret_note) VALUES (?, ?, ?, ?)",
        [
            (1, "ahmed", "ahmed@test.com", "ahmed's private notes"),
            (2, "sara", "sara@test.com", "sara's private notes"),
            (3, "admin", "admin@test.com", "admin token: SECRET_TOKEN_999"),
        ],
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------------
# Home page
# ------------------------------------------------------------------
@app.route("/")
def home():
    return """
    <h2>Vulnerable Test App</h2>
    <ul>
      <li><a href="/search">SQL Injection Demo (search)</a></li>
      <li><a href="/comment">XSS Demo (comment)</a></li>
      <li><a href="/profile/1">IDOR Demo (profile)</a></li>
      <li><a href="/api/users">API Demo (exposed endpoint)</a></li>
    </ul>
    """


# ------------------------------------------------------------------
# 1) SQL Injection - the query is built with string concatenation on purpose
# ------------------------------------------------------------------
@app.route("/search", methods=["GET", "POST"])
def search():
    result_html = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        db = get_db()
        # !! Danger: intentionally vulnerable to SQL Injection, for testing only
        query = f"SELECT username, email FROM users WHERE username = '{username}'"
        try:
            cursor = db.execute(query)
            rows = cursor.fetchall()
            result_html = "<br>".join(str(r) for r in rows)
        except sqlite3.OperationalError as e:
            # this error message is what the SQLi scanner looks for
            result_html = f"SQL error: you have an error in your sql syntax near '{e}'"

    return f"""
    <h2>Search Users</h2>
    <form method="POST">
        <input type="text" name="username" placeholder="Enter a username">
        <button type="submit">Search</button>
    </form>
    <div>{result_html}</div>
    """


# ------------------------------------------------------------------
# 2) XSS - user input is printed back with no sanitization/escaping
# ------------------------------------------------------------------
@app.route("/comment", methods=["GET", "POST"])
def comment():
    comment_text = ""
    if request.method == "POST":
        comment_text = request.form.get("comment", "")

    # !! Danger: user input is embedded straight into the HTML, no escaping
    return f"""
    <h2>Leave a comment</h2>
    <form method="POST">
        <textarea name="comment" placeholder="Write your comment"></textarea>
        <button type="submit">Submit</button>
    </form>
    <div>Comment: {comment_text}</div>
    """


# ------------------------------------------------------------------
# 3) IDOR - anyone can view any user's data just by changing the ID
# ------------------------------------------------------------------
@app.route("/profile/<int:user_id>")
def profile(user_id):
    db = get_db()
    # !! Danger: no check that the current user actually owns this ID
    cursor = db.execute("SELECT username, email, secret_note FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        return "User not found", 404

    return f"""
    <h2>Profile #{user_id}</h2>
    <p>Username: {row[0]}</p>
    <p>Email: {row[1]}</p>
    <p>Secret note: {row[2]}</p>
    """


# ------------------------------------------------------------------
# 4) API - endpoint returning every user's data with no auth
# ------------------------------------------------------------------
@app.route("/api/users")
def api_users():
    db = get_db()
    cursor = db.execute("SELECT id, username, email FROM users")
    rows = cursor.fetchall()
    users = [{"id": r[0], "username": r[1], "email": r[2]} for r in rows]
    return {"users": users}


# ------------------------------------------------------------------
# 5) Missing Security Headers - intentionally no protective headers set
# (the Security Headers scanner picks this up automatically, no extra code needed)
# ------------------------------------------------------------------


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
