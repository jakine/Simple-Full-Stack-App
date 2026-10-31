import { useCallback, useEffect, useState } from "react";
import { api, apiList } from "../api/client";
import { useRole } from "../context/AuthContext";
import TaskPanel from "./TaskPanel";
import { ErrorText, Field, PRIORITIES, PriorityBadge, WorkTypeOptions, defaultPhaseId, styles } from "./ui";

const emptyTask = {
  title: "",
  project: "",
  phase: "",
  priority: "medium",
  team: "",
  work_type: "",
  start_date: "",
  due_date: "",
  planned_quantity: "",
};

const columnStyle = {
  background: "var(--surface-2)",
  borderRadius: "var(--radius)",
  padding: "0.7rem",
  minWidth: "240px",
  flex: "1 0 240px",
  display: "grid",
  gap: "0.5rem",
  alignContent: "start",
  minHeight: "12rem",
  border: "1px solid var(--line)",
};

const cardStyle = {
  background: "var(--surface)",
  border: "1px solid var(--line)",
  borderRadius: "var(--radius-sm)",
  padding: "0.7rem 0.75rem",
  cursor: "grab",
  display: "grid",
  gap: "0.35rem",
  boxShadow: "var(--shadow)",
};

function TaskCard({ task, showProject, dragging, onOpen, onDragStart, onDragEnd, onDropBefore }) {
  return (
    <div
      draggable
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(task.id));
        onDragStart(task.id);
      }}
      onDragEnd={onDragEnd}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onDropBefore(task);
      }}
      onClick={() => onOpen(task.id)}
      style={{ ...cardStyle, opacity: dragging ? 0.4 : 1 }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem", fontSize: "0.78rem", color: "var(--faint)" }}>
        <span>{task.key}</span>
        <PriorityBadge value={task.priority} />
      </div>
      <strong style={{ fontSize: "0.95rem" }}>{task.title}</strong>
      <div style={{ fontSize: "0.8rem", color: "var(--muted)", display: "grid", gap: "0.15rem" }}>
        {showProject && <span>{task.project_name}</span>}
        <span>
          {task.phase_name}
          {task.work_type_name ? ` · ${task.work_type_name}` : ""}
          {task.team_name ? ` · Team ${task.team_number}` : ""}
        </span>
        {task.due_date && <span>Due {task.due_date}</span>}
        {task.progress_percent != null && (
          <div style={{ height: "5px", background: "var(--line)", borderRadius: "3px", overflow: "hidden" }}>
            <div
              style={{
                width: `${Math.min(Number(task.progress_percent), 100)}%`,
                height: "100%",
                background: "var(--accent)",
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function TaskBoard({ projectId }) {
  const { canManage } = useRole();
  const [statuses, setStatuses] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [teams, setTeams] = useState([]);
  const [projectTeams, setProjectTeams] = useState([]);
  const [workTypes, setWorkTypes] = useState([]);
  const [phases, setPhases] = useState([]);
  const [filters, setFilters] = useState({ project: "", team: "", phase: "", search: "" });
  const [form, setForm] = useState({ ...emptyTask, project: projectId ? String(projectId) : "" });
  const [showCreate, setShowCreate] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [dragId, setDragId] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    const project = projectId || filters.project;
    if (project) params.set("project", project);
    if (filters.team) params.set("team", filters.team);
    if (filters.phase) params.set("phase", filters.phase);
    if (filters.search) params.set("search", filters.search);
    const query = params.toString();
    const [statusRows, taskRows] = await Promise.all([
      apiList("/task-statuses/"),
      apiList(`/tasks/${query ? `?${query}` : ""}`),
    ]);
    setStatuses(statusRows);
    setTasks(taskRows);
  }, [projectId, filters]);

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [load]);

  useEffect(() => {
    Promise.all([
      projectId ? Promise.resolve([]) : apiList("/projects/"),
      apiList("/teams/"),
      apiList("/work-types/"),
      apiList("/task-phases/"),
    ])
      .then(([projectRows, teamRows, typeRows, phaseRows]) => {
        setProjects(projectRows);
        setTeams(teamRows);
        setWorkTypes(typeRows);
        setPhases(phaseRows);
        setForm((current) => (current.phase ? current : { ...current, phase: defaultPhaseId(phaseRows) }));
      })
      .catch((err) => setError(err.message));
  }, [projectId]);

  useEffect(() => {
    if (!form.project) {
      setProjectTeams([]);
      return;
    }
    apiList(`/workplace-teams/?workplace=${form.project}`)
      .then(setProjectTeams)
      .catch((err) => setError(err.message));
  }, [form.project]);

  function setFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value, ...(key === "project" ? { team: "" } : {}) }));
  }

  async function createTask(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/tasks/", {
        method: "POST",
        body: {
          title: form.title,
          project: Number(form.project),
          phase: form.phase ? Number(form.phase) : undefined,
          priority: form.priority,
          team: form.team ? Number(form.team) : null,
          work_type: form.work_type ? Number(form.work_type) : null,
          start_date: form.start_date || null,
          due_date: form.due_date || null,
          planned_quantity: form.planned_quantity || null,
        },
      });
      setForm({ ...emptyTask, project: form.project, phase: form.phase });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function dropInto(statusId, beforeTask) {
    const task = tasks.find((row) => row.id === dragId);
    setDragId(null);
    if (!task || (beforeTask && beforeTask.id === task.id)) return;
    const column = tasks.filter((row) => row.status === statusId && row.id !== task.id);
    const index = beforeTask ? column.findIndex((row) => row.id === beforeTask.id) : column.length;
    const position = column.slice(0, index).filter((row) => row.project === task.project).length;

    const moved = { ...task, status: statusId };
    const rest = tasks.filter((row) => row.id !== task.id);
    const insertAt = beforeTask ? rest.findIndex((row) => row.id === beforeTask.id) : rest.length;
    setTasks([...rest.slice(0, insertAt), moved, ...rest.slice(insertAt)]);

    setError("");
    try {
      await api(`/tasks/${task.id}/move/`, { method: "POST", body: { status: statusId, position } });
    } catch (err) {
      setError(err.message);
    }
    await load().catch((err) => setError(err.message));
  }

  const showProject = !projectId;

  return (
    <div style={styles.page}>
      <div style={{ ...styles.card, ...styles.row }}>
        {!projectId && (
          <Field label="Project">
            <select style={styles.input} value={filters.project} onChange={(e) => setFilter("project", e.target.value)}>
              <option value="">All projects</option>
              {projects.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="Team">
          <select style={styles.input} value={filters.team} onChange={(e) => setFilter("team", e.target.value)}>
            <option value="">All teams</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.number} · {team.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Phase">
          <select style={styles.input} value={filters.phase} onChange={(e) => setFilter("phase", e.target.value)}>
            <option value="">All phases</option>
            {phases.map((phase) => (
              <option key={phase.id} value={phase.id}>
                {phase.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Search">
          <input style={styles.input} value={filters.search} onChange={(e) => setFilter("search", e.target.value)} placeholder="Title or text" />
        </Field>
        {canManage && (
          <button type="button" style={styles.button} onClick={() => setShowCreate((value) => !value)}>
            {showCreate ? "Hide new task" : "New task"}
          </button>
        )}
      </div>

      {canManage && showCreate && (
        <form onSubmit={createTask} style={styles.card}>
          <div style={styles.row}>
            <Field label="Title">
              <input style={{ ...styles.input, minWidth: "16rem" }} value={form.title} onChange={(e) => setField("title", e.target.value)} required />
            </Field>
            {!projectId && (
              <Field label="Project">
                <select style={styles.input} value={form.project} onChange={(e) => setField("project", e.target.value)} required>
                  <option value="">Choose</option>
                  {projects.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.name}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            <Field label="Phase">
              <select style={styles.input} value={form.phase} onChange={(e) => setField("phase", e.target.value)}>
                {phases.map((phase) => (
                  <option key={phase.id} value={phase.id}>
                    {phase.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Priority">
              <select style={styles.input} value={form.priority} onChange={(e) => setField("priority", e.target.value)}>
                {PRIORITIES.map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Team">
              <select style={styles.input} value={form.team} onChange={(e) => setField("team", e.target.value)}>
                <option value="">No team</option>
                {projectTeams.map((row) => (
                  <option key={row.id} value={row.team}>
                    {row.team_number} · {row.team_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Work type">
              <select style={styles.input} value={form.work_type} onChange={(e) => setField("work_type", e.target.value)}>
                <option value="">Same as project</option>
                <WorkTypeOptions types={workTypes} />
              </select>
            </Field>
            <Field label="Start">
              <input style={styles.input} type="date" value={form.start_date} onChange={(e) => setField("start_date", e.target.value)} />
            </Field>
            <Field label="Due">
              <input style={styles.input} type="date" value={form.due_date} onChange={(e) => setField("due_date", e.target.value)} />
            </Field>
            <Field
              label={
                workTypes.find((type) => String(type.id) === String(form.work_type))?.measure_symbol
                  ? `Planned (${workTypes.find((type) => String(type.id) === String(form.work_type)).measure_symbol})`
                  : "Planned amount"
              }
            >
              <input
                style={styles.input}
                type="number"
                min="0.01"
                step="0.01"
                value={form.planned_quantity}
                onChange={(e) => setField("planned_quantity", e.target.value)}
              />
            </Field>
            <button style={styles.button} type="submit">
              Add task
            </button>
          </div>
        </form>
      )}

      <ErrorText>{error}</ErrorText>

      <div style={{ display: "flex", gap: "0.75rem", overflowX: "auto", paddingBottom: "0.5rem" }}>
        {statuses.map((status) => {
          const column = tasks.filter((task) => task.status === status.id);
          return (
            <section
              key={status.id}
              style={columnStyle}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                dropInto(status.id, null);
              }}
            >
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ color: status.category_color || "var(--ink)" }}>{status.name}</strong>
                <span style={{ color: "var(--faint)", fontSize: "0.85rem" }}>{column.length}</span>
              </header>
              {column.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  showProject={showProject}
                  dragging={dragId === task.id}
                  onOpen={setSelectedId}
                  onDragStart={setDragId}
                  onDragEnd={() => setDragId(null)}
                  onDropBefore={(before) => dropInto(status.id, before)}
                />
              ))}
              {column.length === 0 && <p style={{ color: "var(--faint)", fontSize: "0.85rem", margin: 0 }}>Drop tasks here</p>}
            </section>
          );
        })}
      </div>
      {statuses.length === 0 && <p>No statuses yet. Add them under Settings → Workflow.</p>}

      {selectedId && (
        <TaskPanel
          taskId={selectedId}
          statuses={statuses}
          onClose={() => setSelectedId(null)}
          onChange={() => load().catch((err) => setError(err.message))}
        />
      )}
    </div>
  );
}

export default TaskBoard;
