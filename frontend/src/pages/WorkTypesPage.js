import { useEffect, useState } from "react";
import { api, apiList } from "../api/client";
import { ErrorText, Field, styles } from "../components/ui";

function WorkTypesPage() {
  const [measures, setMeasures] = useState([]);
  const [types, setTypes] = useState([]);
  const [measureForm, setMeasureForm] = useState({ name: "", symbol: "" });
  const [typeForm, setTypeForm] = useState({ name: "", measure: "" });
  const [error, setError] = useState("");

  async function load() {
    const [measureRows, typeRows] = await Promise.all([apiList("/work-measures/"), apiList("/work-types/")]);
    setMeasures(measureRows);
    setTypes(typeRows);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  async function addMeasure(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/work-measures/", { method: "POST", body: measureForm });
      setMeasureForm({ name: "", symbol: "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function addType(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/work-types/", {
        method: "POST",
        body: { name: typeForm.name, measure: Number(typeForm.measure) },
      });
      setTypeForm({ name: "", measure: "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Work types</h1>
      <p style={{ margin: 0 }}>
        Add a way to measure the work, such as square meters or cubic meters. Each work type uses one of those measures.
      </p>
      <ErrorText>{error}</ErrorText>

      <form onSubmit={addMeasure} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>Measure</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input
              style={styles.input}
              value={measureForm.name}
              onChange={(e) => setMeasureForm({ ...measureForm, name: e.target.value })}
              placeholder="Square meters"
              required
            />
          </Field>
          <Field label="Symbol">
            <input
              style={styles.input}
              value={measureForm.symbol}
              onChange={(e) => setMeasureForm({ ...measureForm, symbol: e.target.value })}
              placeholder="m²"
              required
            />
          </Field>
          <button style={styles.button} type="submit">
            Add measure
          </button>
        </div>
        {measures.length > 0 && (
          <p>{measures.map((measure) => `${measure.name} (${measure.symbol})`).join(", ")}</p>
        )}
      </form>

      <form onSubmit={addType} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>Work type</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input
              style={styles.input}
              value={typeForm.name}
              onChange={(e) => setTypeForm({ ...typeForm, name: e.target.value })}
              required
            />
          </Field>
          <Field label="Measure">
            <select
              style={styles.input}
              value={typeForm.measure}
              onChange={(e) => setTypeForm({ ...typeForm, measure: e.target.value })}
              required
            >
              <option value="">Choose</option>
              {measures.map((measure) => (
                <option key={measure.id} value={measure.id}>
                  {measure.name} ({measure.symbol})
                </option>
              ))}
            </select>
          </Field>
          <button style={styles.button} type="submit">
            Add type
          </button>
        </div>
        {types.length === 0 ? (
          <p>No work types yet.</p>
        ) : (
          <ul>
            {types.map((type) => (
              <li key={type.id}>
                {type.name} · {type.measure_symbol}
              </li>
            ))}
          </ul>
        )}
      </form>
    </div>
  );
}

export default WorkTypesPage;
