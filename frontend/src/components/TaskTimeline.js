import { useCallback, useEffect, useMemo, useState } from "react";
import { apiList } from "../api/client";
import TaskPanel from "./TaskPanel";
import { ErrorText, Field, PriorityBadge, styles } from "./ui";

function parseDate(value) {
  if (!value) return null;
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfWeek(date) {
  const next = new Date(date);
  const weekday = (next.getDay() + 6) % 7;
  next.setDate(next.getDate() - weekday);
  next.setHours(0, 0, 0, 0);
  return next;
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function endOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

function taskSpan(task) {
  const start = parseDate(task.start_date);
  const due = parseDate(task.due_date);
  if (start && due) return { start, end: due };
  if (start) return { start, end: start };
  if (due) return { start: due, end: due };
  return null;
}

function buildColumns(rangeStart, rangeEnd, scale) {
  const columns = [];
  if (scale === "day") {
    let cursor = new Date(rangeStart);
    cursor.setHours(0, 0, 0, 0);
    const last = new Date(rangeEnd);
    last.setHours(0, 0, 0, 0);
    while (cursor <= last) {
      columns.push({
        key: isoDate(cursor),
        label: cursor.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        start: new Date(cursor),
        end: new Date(cursor),
      });
      cursor = addDays(cursor, 1);
    }
    return columns;
  }
  if (scale === "month") {
    let cursor = startOfMonth(rangeStart);
    const last = startOfMonth(rangeEnd);
    while (cursor <= last) {
      columns.push({
        key: isoDate(cursor),
        label: cursor.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
        start: new Date(cursor),
        end: endOfMonth(cursor),
      });
      cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
    }
    return columns;
  }
  let cursor = startOfWeek(rangeStart);
  const last = startOfWeek(rangeEnd);
  while (cursor <= last) {
    columns.push({
      key: isoDate(cursor),
      label: cursor.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      start: new Date(cursor),
      end: addDays(cursor, 6),
    });
    cursor = addDays(cursor, 7);
  }
  return columns;
}

function barStyle(span, rangeStart, rangeEnd) {
  const total = Math.max(rangeEnd.getTime() - rangeStart.getTime(), 1);
  const start = Math.max(span.start.getTime(), rangeStart.getTime());
  const end = Math.min(addDays(span.end, 1).getTime(), addDays(rangeEnd, 1).getTime());
  const left = ((start - rangeStart.getTime()) / total) * 100;
  const width = Math.max(((end - start) / total) * 100, 2);
  return {
    position: "absolute",
    left: `${left}%`,
    width: `${width}%`,
    top: "8px",
    bottom: "8px",
    background: "var(--accent)",
    color: "var(--accent-ink)",
    borderRadius: "4px",
    padding: "0 0.45rem",
    fontSize: "0.78rem",
    display: "flex",
    alignItems: "center",
    gap: "0.4rem",
    overflow: "hidden",
    cursor: "pointer",
    border: "none",
    textAlign: "left",
  };
}

function TaskTimeline({ projectId }) {
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [teams, setTeams] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [phases, setPhases] = useState([]);
  const [filters, setFilters] = useState({ project: "", team: "", phase: "" });
  const [groupBy, setGroupBy] = useState("phase");
  const [durationUnits, setDurationUnits] = useState([]);
  const [scale, setScale] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    const project = projectId || filters.project;
    if (project) params.set("project", project);
    if (filters.team) params.set("team", filters.team);
    if (filters.phase) params.set("phase", filters.phase);
    const query = params.toString();
    const [taskRows, statusRows, phaseRows] = await Promise.all([
      apiList(`/tasks/${query ? `?${query}` : ""}`),
      apiList("/task-statuses/"),
      apiList("/task-phases/"),
    ]);
    setTasks(taskRows);
    setStatuses(statusRows);
    setPhases(phaseRows);
  }, [projectId, filters]);

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [load]);

  useEffect(() => {
    Promise.all([
      projectId ? Promise.resolve([]) : apiList("/projects/"),
      apiList("/teams/"),
      apiList("/duration-units/"),
    ])
      .then(([projectRows, teamRows, unitRows]) => {
        setProjects(projectRows);
        setTeams(teamRows);
        const scales = unitRows.filter((unit) => unit.timeline_step);
        setDurationUnits(scales);
        setScale((current) => {
          if (current && scales.some((unit) => String(unit.id) === String(current))) return current;
          const week = scales.find((unit) => unit.timeline_step === "week") || scales[0];
          return week ? String(week.id) : "";
        });
      })
      .catch((err) => setError(err.message));
  }, [projectId]);

  const dated = useMemo(
    () => tasks.map((task) => ({ task, span: taskSpan(task) })).filter((row) => row.span),
    [tasks]
  );
  const unscheduled = useMemo(() => tasks.filter((task) => !taskSpan(task)), [tasks]);

  const range = useMemo(() => {
    if (dated.length === 0) return null;
    let min = dated[0].span.start;
    let max = dated[0].span.end;
    dated.forEach(({ span }) => {
      if (span.start < min) min = span.start;
      if (span.end > max) max = span.end;
    });
    const selected = durationUnits.find((unit) => String(unit.id) === String(scale));
    const step = selected?.timeline_step || "week";
    if (step === "month") return { start: startOfMonth(min), end: endOfMonth(max) };
    if (step === "day") return { start: min, end: max };
    return { start: startOfWeek(min), end: addDays(startOfWeek(max), 6) };
  }, [dated, durationUnits, scale]);

  const selectedScale = durationUnits.find((unit) => String(unit.id) === String(scale));
  const scaleStep = selectedScale?.timeline_step || "week";
  const columns = range ? buildColumns(range.start, range.end, scaleStep) : [];

  const groups = useMemo(() => {
    if (groupBy === "team") {
      const names = new Map();
      tasks.forEach((task) => {
        const key = task.team ? String(task.team) : "none";
        if (!names.has(key)) {
          names.set(key, task.team_name ? `${task.team_number} · ${task.team_name}` : "No team");
        }
      });
      return [...names.entries()].map(([key, label]) => ({
        key,
        label,
        items: dated.filter(({ task }) => String(task.team || "none") === key),
      }));
    }
    return phases
      .map((phase) => ({
        key: String(phase.id),
        label: phase.name,
        items: dated.filter(({ task }) => String(task.phase) === String(phase.id)),
      }))
      .filter((group) => group.items.length > 0);
  }, [dated, groupBy, phases, tasks]);

  function setFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

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
        <Field label="Group by">
          <select style={styles.input} value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            <option value="phase">Phase</option>
            <option value="team">Team</option>
          </select>
        </Field>
        <Field label="Scale">
          <select style={styles.input} value={scale} onChange={(e) => setScale(e.target.value)}>
            {durationUnits.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.name}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <ErrorText>{error}</ErrorText>

      {range ? (
        <div style={{ ...styles.card, overflowX: "auto" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "160px 1fr",
              minWidth: `${Math.max(columns.length * 88, 640) + 160}px`,
            }}
          >
            <div />
            <div
              style={{
                display: "grid",
                gridTemplateColumns: `repeat(${columns.length}, minmax(80px, 1fr))`,
                borderBottom: "1px solid var(--line)",
              }}
            >
              {columns.map((column) => (
                <div key={column.key} style={{ padding: "0.35rem", fontSize: "0.78rem", color: "var(--muted)" }}>
                  {column.label}
                </div>
              ))}
            </div>
            {groups.map((group) => (
              <div key={group.key} style={{ display: "contents" }}>
                <div style={{ padding: "0.75rem 0.5rem 0.75rem 0", fontWeight: 600, alignSelf: "center" }}>
                  {group.label}
                </div>
                <div style={{ display: "grid" }}>
                  {group.items.map(({ task, span }) => (
                    <div
                      key={task.id}
                      style={{
                        position: "relative",
                        height: "44px",
                        backgroundImage: "linear-gradient(to right, var(--line) 1px, transparent 1px)",
                        backgroundSize: `${100 / columns.length}% 100%`,
                      }}
                    >
                      <button type="button" onClick={() => setSelectedId(task.id)} style={barStyle(span, range.start, range.end)}>
                        <span style={{ fontWeight: 600 }}>{task.key}</span>
                        <span>{task.title}</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={styles.card}>
          <p style={{ margin: 0 }}>No scheduled tasks yet. Set a start or due date on a task to see it here.</p>
        </div>
      )}

      {unscheduled.length > 0 && (
        <div style={styles.card}>
          <h2 style={{ marginTop: 0 }}>Unscheduled</h2>
          <ul>
            {unscheduled.map((task) => (
              <li key={task.id} style={{ marginBottom: "0.4rem" }}>
                <button type="button" style={styles.quiet} onClick={() => setSelectedId(task.id)}>
                  {task.key}
                </button>{" "}
                {task.title} · {task.phase_name} <PriorityBadge value={task.priority} />
              </li>
            ))}
          </ul>
        </div>
      )}

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

export default TaskTimeline;
