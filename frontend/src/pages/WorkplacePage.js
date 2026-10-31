import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, apiList } from "../api/client";
import { ErrorText, Field, styles } from "../components/ui";

const crewTable = {
  width: "100%",
  borderCollapse: "separate",
  borderSpacing: "0 0.75rem",
};
const crewHead = { ...styles.th, borderBottom: "none", padding: "0.35rem 1rem" };
const crewCell = {
  padding: "1rem",
  background: "#f7fafa",
  verticalAlign: "top",
};

function lengthLabel(place) {
  if (!place.length_count || !place.length_unit) return "No length set";
  const units = { day: "days", week: "weeks", month: "months" };
  return `${place.length_count} ${units[place.length_unit] || place.length_unit}`;
}

function WorkplacePage() {
  const { id } = useParams();
  const [place, setPlace] = useState(null);
  const [teams, setTeams] = useState([]);
  const [teamPlacement, setTeamPlacement] = useState({ team: "", start_date: "" });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const [detail, teamRows] = await Promise.all([api(`/workplaces/${id}/`), apiList("/teams/")]);
    setPlace(detail);
    setTeams(teamRows);
  }, [id]);

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [load]);

  async function placeTeam(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/workplace-teams/", {
        method: "POST",
        body: {
          workplace: Number(id),
          team: Number(teamPlacement.team),
          start_date: teamPlacement.start_date,
        },
      });
      setTeamPlacement({ team: "", start_date: "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeTeam(rowId) {
    setError("");
    try {
      await api(`/workplace-teams/${rowId}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!place) return <ErrorText>{error || "Loading..."}</ErrorText>;

  const placedIds = new Set((place.teams || []).map((row) => row.team));

  return (
    <div style={styles.page}>
      <div>
        <Link to="/contracts">Contracts</Link>
        <h1 style={{ marginBottom: 0 }}>{place.name}</h1>
        <p>
          {lengthLabel(place)}
          {place.work_type_name ? ` · ${place.work_type_name}` : ""}
          {place.measure_symbol && place.planned_quantity != null
            ? ` · planned ${place.planned_quantity} ${place.measure_symbol}`
            : ""}
        </p>
        <p>
          Done {place.done_quantity}
          {place.measure_symbol ? ` ${place.measure_symbol}` : ""}
          {place.remaining_quantity != null
            ? ` · remaining ${place.remaining_quantity}${place.measure_symbol ? ` ${place.measure_symbol}` : ""}`
            : ""}
          {place.progress_percent != null ? ` · ${place.progress_percent}%` : ""}
          {` · ${place.days_worked} days worked`}
        </p>
        <Link to={`/reports?workplace=${place.id}`}>Fill a report</Link>
      </div>
      <ErrorText>{error}</ErrorText>

      <form onSubmit={placeTeam} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>Teams on this contract</h2>
        <p style={{ marginTop: 0 }}>Add one team or several. The same team can also work on other contracts.</p>
        <div style={styles.row}>
          <Field label="Team">
            <select
              style={styles.input}
              value={teamPlacement.team}
              onChange={(e) => setTeamPlacement({ ...teamPlacement, team: e.target.value })}
              required
            >
              <option value="">Choose</option>
              {teams
                .filter((team) => !placedIds.has(team.id))
                .map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.number} · {team.name}
                  </option>
                ))}
            </select>
          </Field>
          <Field label="From">
            <input
              style={styles.input}
              type="date"
              value={teamPlacement.start_date}
              onChange={(e) => setTeamPlacement({ ...teamPlacement, start_date: e.target.value })}
              required
            />
          </Field>
          <button style={styles.button} type="submit">
            Place team
          </button>
        </div>
        {(place.teams || []).length === 0 ? (
          <p>No team is on this contract yet.</p>
        ) : (
          <table style={crewTable}>
            <thead>
              <tr>
                <th style={crewHead}>Team</th>
                <th style={crewHead}>Workers</th>
                <th style={crewHead}>Leads</th>
                <th style={crewHead}>From</th>
                <th style={crewHead}></th>
              </tr>
            </thead>
            <tbody>
              {place.teams.map((row) => (
                <tr key={row.id}>
                  <td style={crewCell}>
                    <strong>
                      {row.team_number} · {row.team_name}
                    </strong>
                  </td>
                  <td style={crewCell}>{row.worker_count}</td>
                  <td style={crewCell}>{row.lead_note || "—"}</td>
                  <td style={crewCell}>{row.start_date}</td>
                  <td style={crewCell}>
                    <button type="button" style={styles.danger} onClick={() => removeTeam(row.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </form>
    </div>
  );
}

export default WorkplacePage;
