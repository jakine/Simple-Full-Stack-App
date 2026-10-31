import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, apiList } from "../api/client";
import { ErrorText, Field, styles } from "../components/ui";
import { useRole } from "../context/AuthContext";

const emptyStatus = { name: "", category: "" };
const emptyCategory = { name: "", color: "#01696f" };
const emptyPhase = { name: "" };

function WorkflowSettingsPage() {
  const { canManage } = useRole();
  const [categories, setCategories] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [phases, setPhases] = useState([]);
  const [categoryForm, setCategoryForm] = useState(emptyCategory);
  const [statusForm, setStatusForm] = useState(emptyStatus);
  const [phaseForm, setPhaseForm] = useState(emptyPhase);
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [editingStatusId, setEditingStatusId] = useState(null);
  const [editingPhaseId, setEditingPhaseId] = useState(null);
  const [error, setError] = useState("");

  function load() {
    return Promise.all([apiList("/task-categories/"), apiList("/task-statuses/"), apiList("/task-phases/")]).then(
      ([categoryRows, statusRows, phaseRows]) => {
        setCategories(categoryRows);
        setStatuses(statusRows);
        setPhases(phaseRows);
        setStatusForm((current) =>
          current.category || categoryRows.length === 0
            ? current
            : { ...current, category: String(categoryRows[0].id) }
        );
      }
    );
  }

  useEffect(() => {
    if (!canManage) return undefined;
    load().catch((err) => setError(err.message));
    return undefined;
  }, [canManage]);

  if (!canManage) return <Navigate to="/projects" replace />;

  async function saveCategory(event) {
    event.preventDefault();
    setError("");
    try {
      if (editingCategoryId) {
        await api(`/task-categories/${editingCategoryId}/`, { method: "PATCH", body: categoryForm });
      } else {
        await api("/task-categories/", {
          method: "POST",
          body: { ...categoryForm, position: categories.length },
        });
      }
      setCategoryForm(emptyCategory);
      setEditingCategoryId(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function savePhase(event) {
    event.preventDefault();
    setError("");
    try {
      if (editingPhaseId) {
        await api(`/task-phases/${editingPhaseId}/`, { method: "PATCH", body: phaseForm });
      } else {
        await api("/task-phases/", { method: "POST", body: { ...phaseForm, position: phases.length } });
      }
      setPhaseForm(emptyPhase);
      setEditingPhaseId(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveStatus(event) {
    event.preventDefault();
    setError("");
    try {
      const body = { name: statusForm.name, category: Number(statusForm.category) };
      if (editingStatusId) {
        await api(`/task-statuses/${editingStatusId}/`, { method: "PATCH", body });
      } else {
        await api("/task-statuses/", { method: "POST", body: { ...body, position: statuses.length } });
      }
      setStatusForm({ name: "", category: statusForm.category });
      setEditingStatusId(null);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function reorder(path, ids, setter) {
    setError("");
    try {
      setter(await api(`${path}reorder/`, { method: "POST", body: { ids } }));
    } catch (err) {
      setError(err.message);
      await load().catch((loadErr) => setError(loadErr.message));
    }
  }

  function moveRow(rows, index, offset, path, setter) {
    const next = index + offset;
    if (next < 0 || next >= rows.length) return;
    const ids = rows.map((row) => row.id);
    const [moved] = ids.splice(index, 1);
    ids.splice(next, 0, moved);
    setter(ids.map((id, position) => ({ ...rows.find((row) => row.id === id), position })));
    reorder(path, ids, setter);
  }

  async function remove(path, row, label) {
    if (!window.confirm(`Delete ${label} “${row.name}”? Records still using it cannot be deleted this way.`)) return;
    setError("");
    try {
      await api(`${path}${row.id}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Workflow</h1>
      <p style={{ margin: 0 }}>
        Categories group statuses, such as to do, in progress, or done. Statuses are the columns on the board.
        Phases group tasks on the timeline.
      </p>
      <ErrorText>{error}</ErrorText>

      <form onSubmit={saveCategory} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>{editingCategoryId ? "Edit category" : "Add category"}</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input
              style={styles.input}
              value={categoryForm.name}
              onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
              required
            />
          </Field>
          <Field label="Color">
            <input
              style={{ ...styles.input, padding: "0.2rem", width: "4.5rem", minWidth: "4.5rem" }}
              type="color"
              value={categoryForm.color}
              onChange={(e) => setCategoryForm({ ...categoryForm, color: e.target.value })}
            />
          </Field>
          <button style={styles.button} type="submit">
            {editingCategoryId ? "Save" : "Add category"}
          </button>
          {editingCategoryId && (
            <button
              type="button"
              style={styles.quiet}
              onClick={() => {
                setEditingCategoryId(null);
                setCategoryForm(emptyCategory);
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div style={styles.card}>
        {categories.length === 0 ? (
          <p>No categories yet.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Order</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Color</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category, index) => (
                <tr key={category.id}>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(categories, index, -1, "/task-categories/", setCategories)}
                      disabled={index === 0}
                    >
                      Up
                    </button>{" "}
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(categories, index, 1, "/task-categories/", setCategories)}
                      disabled={index === categories.length - 1}
                    >
                      Down
                    </button>
                  </td>
                  <td style={styles.td}>{category.name}</td>
                  <td style={styles.td}>
                    <span
                      style={{
                        display: "inline-block",
                        width: "0.9rem",
                        height: "0.9rem",
                        borderRadius: "3px",
                        background: category.color,
                        verticalAlign: "middle",
                        marginRight: "0.4rem",
                      }}
                    />
                    {category.color}
                  </td>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.button}
                      onClick={() => {
                        setEditingCategoryId(category.id);
                        setCategoryForm({ name: category.name, color: category.color });
                      }}
                    >
                      Edit
                    </button>{" "}
                    <button
                      type="button"
                      style={styles.danger}
                      onClick={() => remove("/task-categories/", category, "category")}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form onSubmit={saveStatus} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>{editingStatusId ? "Edit status" : "Add status"}</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input
              style={styles.input}
              value={statusForm.name}
              onChange={(e) => setStatusForm({ ...statusForm, name: e.target.value })}
              required
            />
          </Field>
          <Field label="Category">
            <select
              style={styles.input}
              value={statusForm.category}
              onChange={(e) => setStatusForm({ ...statusForm, category: e.target.value })}
              required
            >
              <option value="">Choose</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </Field>
          <button style={styles.button} type="submit">
            {editingStatusId ? "Save" : "Add status"}
          </button>
          {editingStatusId && (
            <button
              type="button"
              style={styles.quiet}
              onClick={() => {
                setEditingStatusId(null);
                setStatusForm({ name: "", category: categories[0] ? String(categories[0].id) : "" });
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div style={styles.card}>
        {statuses.length === 0 ? (
          <p>No statuses yet.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Order</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Category</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {statuses.map((status, index) => (
                <tr key={status.id}>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(statuses, index, -1, "/task-statuses/", setStatuses)}
                      disabled={index === 0}
                    >
                      Up
                    </button>{" "}
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(statuses, index, 1, "/task-statuses/", setStatuses)}
                      disabled={index === statuses.length - 1}
                    >
                      Down
                    </button>
                  </td>
                  <td style={styles.td}>{status.name}</td>
                  <td style={styles.td}>
                    <span style={{ color: status.category_color }}>{status.category_name}</span>
                  </td>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.button}
                      onClick={() => {
                        setEditingStatusId(status.id);
                        setStatusForm({ name: status.name, category: String(status.category) });
                      }}
                    >
                      Edit
                    </button>{" "}
                    <button type="button" style={styles.danger} onClick={() => remove("/task-statuses/", status, "status")}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form onSubmit={savePhase} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>{editingPhaseId ? "Edit phase" : "Add phase"}</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input
              style={styles.input}
              value={phaseForm.name}
              onChange={(e) => setPhaseForm({ name: e.target.value })}
              placeholder="Close-out"
              required
            />
          </Field>
          <button style={styles.button} type="submit">
            {editingPhaseId ? "Save" : "Add phase"}
          </button>
          {editingPhaseId && (
            <button
              type="button"
              style={styles.quiet}
              onClick={() => {
                setEditingPhaseId(null);
                setPhaseForm(emptyPhase);
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div style={styles.card}>
        {phases.length === 0 ? (
          <p>No phases yet.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Order</th>
                <th style={styles.th}>Phase</th>
                <th style={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {phases.map((phase, index) => (
                <tr key={phase.id}>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(phases, index, -1, "/task-phases/", setPhases)}
                      disabled={index === 0}
                    >
                      Up
                    </button>{" "}
                    <button
                      type="button"
                      style={styles.quiet}
                      onClick={() => moveRow(phases, index, 1, "/task-phases/", setPhases)}
                      disabled={index === phases.length - 1}
                    >
                      Down
                    </button>
                  </td>
                  <td style={styles.td}>{phase.name}</td>
                  <td style={styles.td}>
                    <button
                      type="button"
                      style={styles.button}
                      onClick={() => {
                        setEditingPhaseId(phase.id);
                        setPhaseForm({ name: phase.name });
                      }}
                    >
                      Edit
                    </button>{" "}
                    <button type="button" style={styles.danger} onClick={() => remove("/task-phases/", phase, "phase")}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default WorkflowSettingsPage;
