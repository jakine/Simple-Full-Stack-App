import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiList } from "../api/client";
import { ErrorText, Field, WorkTypeOptions, styles } from "../components/ui";
import { useRole } from "../context/AuthContext";

const emptyForm = {
  name: "",
  address: "",
  status: "planned",
  length_count: "",
  length_unit: "",
  work_type: "",
  planned_quantity: "",
};

function lengthLabel(row) {
  if (!row.length_count || !row.length_unit) return "";
  const unit = row.length_unit_name || "";
  const days = row.length_days != null ? ` (${row.length_days} days)` : "";
  return `${row.length_count} ${unit}${days}`;
}

function ProjectsPage() {
  const { canManage } = useRole();
  const [places, setPlaces] = useState([]);
  const [workTypes, setWorkTypes] = useState([]);
  const [durationUnits, setDurationUnits] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");

  async function load() {
    const [projectRows, typeRows, unitRows] = await Promise.all([
      apiList("/projects/"),
      apiList("/work-types/"),
      apiList("/duration-units/"),
    ]);
    setPlaces(projectRows);
    setWorkTypes(typeRows);
    setDurationUnits(unitRows);
    setForm((current) => {
      if (current.length_unit) return current;
      const day = unitRows.find((unit) => unit.symbol === "day") || unitRows[0];
      return day ? { ...current, length_unit: String(day.id) } : current;
    });
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const selectedType = workTypes.find((type) => String(type.id) === String(form.work_type));

  async function createProject(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/projects/", {
        method: "POST",
        body: {
          name: form.name,
          address: form.address,
          status: form.status,
          length_count: Number(form.length_count),
          length_unit: form.length_unit ? Number(form.length_unit) : null,
          work_type: form.work_type ? Number(form.work_type) : null,
          planned_quantity: form.planned_quantity || null,
        },
      });
      setForm({
        ...emptyForm,
        length_unit: form.length_unit,
      });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Projects</h1>
      <p style={{ margin: 0 }}>
        A project has a length in addable duration units, converted to days. One or more teams can work on it, and a
        team can be on more than one project.
      </p>
      <ErrorText>{error}</ErrorText>
      {canManage && (
      <form onSubmit={createProject} style={styles.card}>
        <div style={styles.row}>
          <Field label="Name">
            <input style={styles.input} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </Field>
          <Field label="Address">
            <input style={styles.input} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </Field>
          <Field label="Length">
            <input
              style={styles.input}
              type="number"
              min="1"
              step="1"
              value={form.length_count}
              onChange={(e) => setForm({ ...form, length_count: e.target.value })}
              required
            />
          </Field>
          <Field label="Unit">
            <select style={styles.input} value={form.length_unit} onChange={(e) => setForm({ ...form, length_unit: e.target.value })}>
              {durationUnits.map((unit) => (
                <option key={unit.id} value={unit.id}>
                  {unit.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Type of work">
            <select style={styles.input} value={form.work_type} onChange={(e) => setForm({ ...form, work_type: e.target.value })}>
              <option value="">None yet</option>
              <WorkTypeOptions types={workTypes} />
            </select>
          </Field>
          <Field label={selectedType ? `Planned (${selectedType.measure_symbol})` : "Planned amount"}>
            <input
              style={styles.input}
              type="number"
              min="0.01"
              step="0.01"
              value={form.planned_quantity}
              onChange={(e) => setForm({ ...form, planned_quantity: e.target.value })}
            />
          </Field>
          <button style={styles.button} type="submit">
            Add project
          </button>
        </div>
      </form>
      )}
      <div style={styles.card}>
        {places.length === 0 ? (
          <p>No projects yet.</p>
        ) : (
          <ul>
            {places.map((place) => (
              <li key={place.id}>
                <Link to={`/projects/${place.id}`}>{place.name}</Link>
                {lengthLabel(place) ? ` · ${lengthLabel(place)}` : ""}
                {place.work_type_name
                  ? ` · ${place.work_type_category_name ? `${place.work_type_category_name} · ` : ""}${place.work_type_name}`
                  : ""}
                {place.progress_percent != null ? ` · ${place.progress_percent}%` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ProjectsPage;
