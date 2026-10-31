import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, apiList } from "../api/client";
import { ErrorText, Field, styles } from "../components/ui";

const emptyForm = {
  name: "",
  address: "",
  status: "planned",
  length_count: "",
  length_unit: "day",
  work_type: "",
  planned_quantity: "",
};

function lengthLabel(row) {
  if (!row.length_count || !row.length_unit) return "";
  const units = { day: "days", week: "weeks", month: "months" };
  return `${row.length_count} ${units[row.length_unit] || row.length_unit}`;
}

function WorkplacesPage() {
  const [places, setPlaces] = useState([]);
  const [workTypes, setWorkTypes] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");

  async function load() {
    const [contractRows, typeRows] = await Promise.all([apiList("/workplaces/"), apiList("/work-types/")]);
    setPlaces(contractRows);
    setWorkTypes(typeRows);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const selectedType = workTypes.find((type) => String(type.id) === String(form.work_type));

  async function createContract(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/workplaces/", {
        method: "POST",
        body: {
          name: form.name,
          address: form.address,
          status: form.status,
          length_count: Number(form.length_count),
          length_unit: form.length_unit,
          work_type: form.work_type ? Number(form.work_type) : null,
          planned_quantity: form.planned_quantity || null,
        },
      });
      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Contracts</h1>
      <p style={{ margin: 0 }}>
        A contract is work for a number of days, weeks, or months. One or more teams can work on it, and a team can be on more than one contract.
      </p>
      <ErrorText>{error}</ErrorText>
      <form onSubmit={createContract} style={styles.card}>
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
              <option value="day">Days</option>
              <option value="week">Weeks</option>
              <option value="month">Months</option>
            </select>
          </Field>
          <Field label="Type of work">
            <select style={styles.input} value={form.work_type} onChange={(e) => setForm({ ...form, work_type: e.target.value })}>
              <option value="">None yet</option>
              {workTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name} ({type.measure_symbol})
                </option>
              ))}
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
            Add contract
          </button>
        </div>
      </form>
      <div style={styles.card}>
        {places.length === 0 ? (
          <p>No contracts yet.</p>
        ) : (
          <ul>
            {places.map((place) => (
              <li key={place.id}>
                <Link to={`/contracts/${place.id}`}>{place.name}</Link>
                {lengthLabel(place) ? ` · ${lengthLabel(place)}` : ""}
                {place.work_type_name ? ` · ${place.work_type_name}` : ""}
                {place.progress_percent != null ? ` · ${place.progress_percent}%` : ""}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default WorkplacesPage;
