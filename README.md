# Task Manager

A small full-stack task manager.

- **Backend:** Python, Flask, SQLite (SQL, parameterised queries)
- **API:** JSON REST endpoints with input validation
- **Frontend:** React (via CDN), JavaScript, HTML, CSS
- **Tests:** unittest for the API
- **Version control:** Git

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 (needs internet for the React CDN scripts and font).

## Run the tests

```bash
python -m unittest test_api
```

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/tasks?status=all\|active\|done | List tasks |
| POST | /api/tasks | Create (title, priority, due_date) |
| PATCH | /api/tasks/<id> | Update title, priority, due_date or done |
| DELETE | /api/tasks/<id> | Delete a task |

## Put it on GitHub

```bash
git init
git add .
git commit -m "Initial task manager"
```
