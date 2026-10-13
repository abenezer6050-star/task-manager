const { useState, useEffect, useCallback } = React;

const API = "/api/tasks";

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function todayString() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function AddTaskForm({ onAdd }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    const ok = await onAdd({ title, priority, due_date: dueDate || null });
    if (ok) {
      setTitle("");
      setDueDate("");
      setPriority("medium");
    }
  }

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <input
        className="title-input"
        type="text"
        placeholder="What needs doing?"
        aria-label="Task title"
        value={title}
        maxLength={200}
        onChange={(e) => setTitle(e.target.value)}
      />
      <select
        aria-label="Priority"
        value={priority}
        onChange={(e) => setPriority(e.target.value)}
      >
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>
      <input
        type="date"
        aria-label="Due date"
        value={dueDate}
        onChange={(e) => setDueDate(e.target.value)}
      />
      <button className="primary" type="submit">Add task</button>
    </form>
  );
}

function TaskItem({ task, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(task.title);
  const overdue = !task.done && task.due_date && task.due_date < todayString();

  async function saveEdit() {
    const ok = await onUpdate(task.id, { title: draft });
    if (ok) setEditing(false);
  }

  return (
    <li className={`task ${task.priority} ${task.done ? "done" : ""}`}>
      <input
        type="checkbox"
        checked={task.done}
        aria-label={`Mark "${task.title}" as ${task.done ? "not done" : "done"}`}
        onChange={() => onUpdate(task.id, { done: !task.done })}
      />
      <div className="task-main">
        {editing ? (
          <input
            className="edit-input"
            type="text"
            aria-label="Edit task title"
            value={draft}
            autoFocus
            maxLength={200}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") saveEdit();
              if (e.key === "Escape") { setEditing(false); setDraft(task.title); }
            }}
          />
        ) : (
          <div className="task-title">{task.title}</div>
        )}
        <div className="task-meta">
          {task.priority} priority
          {task.due_date && (
            <span>
              {" · due "}
              <span className={overdue ? "overdue" : ""}>
                {task.due_date}{overdue ? " (overdue)" : ""}
              </span>
            </span>
          )}
        </div>
      </div>
      <div className="task-actions">
        {editing ? (
          <button onClick={saveEdit}>Save</button>
        ) : (
          <button onClick={() => { setDraft(task.title); setEditing(true); }}>Edit</button>
        )}
        <button className="delete" onClick={() => onDelete(task.id)}>Delete</button>
      </div>
    </li>
  );
}

function App() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadTasks = useCallback(async () => {
    try {
      setTasks(await request(`${API}?status=${filter}`));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  // Each action returns true on success so forms know whether to reset.
  async function run(action) {
    try {
      await action();
      await loadTasks();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  }

  const addTask = (fields) =>
    run(() => request(API, { method: "POST", body: JSON.stringify(fields) }));
  const updateTask = (id, fields) =>
    run(() => request(`${API}/${id}`, { method: "PATCH", body: JSON.stringify(fields) }));
  const deleteTask = (id) =>
    run(() => request(`${API}/${id}`, { method: "DELETE" }));

  const openCount = tasks.filter((t) => !t.done).length;

  return (
    <main className="app">
      <h1>Task Manager</h1>
      <p className="summary">
        {loading ? "Loading…" : `${openCount} open in this view, ${tasks.length} shown`}
      </p>

      <AddTaskForm onAdd={addTask} />
      {error && <div className="error" role="alert">{error}</div>}

      <div className="filters" role="group" aria-label="Filter tasks">
        {["all", "active", "done"].map((f) => (
          <button key={f} aria-pressed={filter === f} onClick={() => setFilter(f)}>
            {f[0].toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {tasks.length === 0 && !loading ? (
        <p className="empty">No tasks here yet. Add one above.</p>
      ) : (
        <ul className="task-list">
          {tasks.map((t) => (
            <TaskItem key={t.id} task={t} onUpdate={updateTask} onDelete={deleteTask} />
          ))}
        </ul>
      )}
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
