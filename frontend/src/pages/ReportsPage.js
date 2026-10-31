import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, apiList } from "../api/client";
import { ErrorText, Field, styles } from "../components/ui";

function today() {
  return new Date().toISOString().slice(0, 10);
}

function ReportsPage() {
  const [searchParams] = useSearchParams();
  const [places, setPlaces] = useState([]);
  const [place, setPlace] = useState(null);
  const [reports, setReports] = useState([]);
  const [workplaceId, setWorkplaceId] = useState(searchParams.get("workplace") || "");
  const [form, setForm] = useState({ work_date: today(), days: "1", team: "", quantity: "", note: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    apiList("/workplaces/")
      .then(setPlaces)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!workplaceId) {
      setPlace(null);
      setReports([]);
      return;
    }
    Promise.all([api(`/workplaces/${workplaceId}/`), apiList(`/site-reports/?workplace=${workplaceId}`)])
      .then(([detail, rows]) => {
        setPlace(detail);
        setReports(rows);
      })
      .catch((err) => setError(err.message));
  }, [workplaceId]);

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function fillReport(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/site-reports/", {
        method: "POST",
        body: {
          workplace: Number(workplaceId),
          team: Number(form.team),
          work_date: form.work_date,
          days: form.days,
          quantity: form.quantity,
          note: form.note,
        },
      });
      setForm({ work_date: form.work_date, days: "1", team: "", quantity: "", note: "" });
      const [detail, rows] = await Promise.all([
        api(`/workplaces/${workplaceId}/`),
        apiList(`/site-reports/?workplace=${workplaceId}`),
      ]);
      setPlace(detail);
      setReports(rows);
    } catch (err) {
      setError(err.message);
    }
  }

  const symbol = place?.measure_symbol;

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Reports</h1>
      <p style={{ margin: 0 }}>
        Record the days a team worked on a contract, and how much of the measured work they finished.
      </p>
      <ErrorText>{error}</ErrorText>
      <div style={styles.card}>
        <Field label="Contract">
          <select style={styles.input} value={workplaceId} onChange={(e) => setWorkplaceId(e.target.value)}>
            <option value="">Choose</option>
            {places.map((row) => (
              <option key={row.id} value={row.id}>
                {row.name}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {place && (
        <form onSubmit={fillReport} style={styles.card}>
          <h2 style={{ marginTop: 0 }}>{place.name}</h2>
          {(place.teams || []).length === 0 && <p>Place a team on this contract before filling a report.</p>}
          <div style={styles.row}>
            <Field label="Team">
              <select style={styles.input} value={form.team} onChange={(e) => setField("team", e.target.value)} required>
                <option value="">Choose</option>
                {(place.teams || []).map((row) => (
                  <option key={row.id} value={row.team}>
                    {row.team_number} · {row.team_name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Date">
              <input style={styles.input} type="date" value={form.work_date} onChange={(e) => setField("work_date", e.target.value)} required />
            </Field>
            <Field label="Days worked">
              <input
                style={styles.input}
                type="number"
                min="0.01"
                step="0.5"
                value={form.days}
                onChange={(e) => setField("days", e.target.value)}
                required
              />
            </Field>
            <Field label={symbol ? `Amount (${symbol})` : "Amount"}>
              <input
                style={styles.input}
                type="number"
                min="0.01"
                step="0.01"
                value={form.quantity}
                onChange={(e) => setField("quantity", e.target.value)}
                required
              />
            </Field>
            <Field label="Note">
              <input style={styles.input} value={form.note} onChange={(e) => setField("note", e.target.value)} />
            </Field>
            <button style={styles.button} type="submit">
              Fill report
            </button>
          </div>
          <table style={{ ...styles.table, marginTop: "1rem" }}>
            <thead>
              <tr>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Team</th>
                <th style={styles.th}>Days</th>
                <th style={styles.th}>Done</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((row) => (
                <tr key={row.id}>
                  <td style={styles.td}>{row.work_date}</td>
                  <td style={styles.td}>
                    {row.team_number} · {row.team_name}
                  </td>
                  <td style={styles.td}>{row.days}</td>
                  <td style={styles.td}>
                    {row.quantity}
                    {row.measure_symbol ? ` ${row.measure_symbol}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {reports.length === 0 && <p>No reports for this contract yet.</p>}
        </form>
      )}
    </div>
  );
}

export default ReportsPage;
