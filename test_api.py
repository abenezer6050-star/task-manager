import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app  # noqa: E402


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app(self.path).test_client()

    def tearDown(self):
        os.remove(self.path)

    def test_create_and_list(self):
        res = self.client.post("/api/tasks", json={"title": "Write CV", "priority": "high"})
        self.assertEqual(res.status_code, 201)
        tasks = self.client.get("/api/tasks").get_json()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["priority"], "high")

    def test_rejects_empty_title(self):
        res = self.client.post("/api/tasks", json={"title": "   "})
        self.assertEqual(res.status_code, 400)

    def test_rejects_bad_date(self):
        res = self.client.post("/api/tasks", json={"title": "x", "due_date": "tomorrow"})
        self.assertEqual(res.status_code, 400)

    def test_toggle_done_and_filter(self):
        task = self.client.post("/api/tasks", json={"title": "a"}).get_json()
        self.client.patch(f"/api/tasks/{task['id']}", json={"done": True})
        self.assertEqual(len(self.client.get("/api/tasks?status=done").get_json()), 1)
        self.assertEqual(len(self.client.get("/api/tasks?status=active").get_json()), 0)

    def test_delete_and_missing(self):
        task = self.client.post("/api/tasks", json={"title": "a"}).get_json()
        self.assertEqual(self.client.delete(f"/api/tasks/{task['id']}").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/tasks/{task['id']}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
