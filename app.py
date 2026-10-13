"""Task Manager: Flask REST API + SQLite, serving a React frontend."""
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request

PRIORITIES = ("low", "medium", "high")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def create_app(db_path=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["DATABASE"] = db_path or os.path.join(app.root_path, "tasks.db")

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        with app.app_context():
            with app.open_resource("schema.sql") as f:
                get_db().executescript(f.read().decode("utf-8"))
            get_db().commit()

    def row_to_dict(row):
        return {
            "id": row["id"],
            "title": row["title"],
            "priority": row["priority"],
            "due_date": row["due_date"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
        }

    def error(message, status=400):
        return jsonify({"error": message}), status

    def validate(data, partial=False):
        """Return (clean_fields, error_message)."""
        clean = {}
        if not isinstance(data, dict):
            return None, "Request body must be JSON."

        if "title" in data or not partial:
            title = str(data.get("title", "")).strip()
            if not title:
                return None, "Title is required."
            if len(title) > 200:
                return None, "Title must be 200 characters or fewer."
            clean["title"] = title

        if "priority" in data:
            if data["priority"] not in PRIORITIES:
                return None, "Priority must be low, medium or high."
            clean["priority"] = data["priority"]

        if "due_date" in data:
            due = data["due_date"] or None
            if due is not None and not DATE_RE.match(str(due)):
                return None, "Due date must look like YYYY-MM-DD."
            clean["due_date"] = due

        if "done" in data:
            if not isinstance(data["done"], bool):
                return None, "Done must be true or false."
            clean["done"] = int(data["done"])

        return clean, None

    # ---------- routes ----------
    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/tasks")
    def list_tasks():
        status = request.args.get("status", "all")
        query = "SELECT * FROM tasks"
        params = []
        if status == "active":
            query += " WHERE done = 0"
        elif status == "done":
            query += " WHERE done = 1"
        elif status != "all":
            return error("Status must be all, active or done.")
        # Open tasks first, then soonest due date, then newest.
        query += (
            " ORDER BY done ASC,"
            " CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,"
            " due_date ASC, id DESC"
        )
        rows = get_db().execute(query, params).fetchall()
        return jsonify([row_to_dict(r) for r in rows])

    @app.post("/api/tasks")
    def create_task():
        clean, msg = validate(request.get_json(silent=True))
        if msg:
            return error(msg)
        db = get_db()
        cur = db.execute(
            "INSERT INTO tasks (title, priority, due_date) VALUES (?, ?, ?)",
            (clean["title"], clean.get("priority", "medium"), clean.get("due_date")),
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(row_to_dict(row)), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id):
        clean, msg = validate(request.get_json(silent=True), partial=True)
        if msg:
            return error(msg)
        if not clean:
            return error("Nothing to update.")
        db = get_db()
        if db.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone() is None:
            return error("Task not found.", 404)
        # Column names come from our own validated keys, never from user input.
        assignments = ", ".join(f"{col} = ?" for col in clean)
        db.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?",
            (*clean.values(), task_id),
        )
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(row_to_dict(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        db = get_db()
        cur = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Task not found.", 404)
        return "", 204

    init_db()
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
