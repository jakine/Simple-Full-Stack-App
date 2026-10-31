import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { ErrorText, styles } from "../components/ui";

function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.active_company) return;
    const until = new Date();
    until.setDate(until.getDate() + 30);
    const expiresBefore = until.toISOString().slice(0, 10);
    Promise.all([
      api("/workers/?page_size=1"),
      api("/workplaces/?page_size=1"),
      api(`/stock-lots/?expires_before=${expiresBefore}&page_size=5`),
    ])
      .then(([workers, workplaces, lots]) => {
        setStats({
          workers: workers.count,
          workplaces: workplaces.count,
          expiring: lots.results || [],
        });
      })
      .catch((err) => setError(err.message));
  }, [user?.active_company]);

  if (!user?.active_company) {
    return (
      <div style={styles.card}>
        <h1>Choose a company</h1>
        <p>Create a company or switch to one you already manage.</p>
        <Link to="/company">Go to company</Link>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Home</h1>
      <ErrorText>{error}</ErrorText>
      {stats && (
        <>
          <div style={styles.stats}>
            <div style={styles.stat}>
              <div style={styles.label}>Workers</div>
              <strong>{stats.workers}</strong>
            </div>
            <div style={styles.stat}>
              <div style={styles.label}>Contracts</div>
              <strong>{stats.workplaces}</strong>
            </div>
            <div style={styles.stat}>
              <div style={styles.label}>Lots expiring in 30 days</div>
              <strong>{stats.expiring.length}</strong>
            </div>
          </div>
          <div style={styles.card}>
            <h2 style={{ marginTop: 0 }}>Expiring stock</h2>
            {stats.expiring.length === 0 ? (
              <p>No lots expire in the next 30 days.</p>
            ) : (
              <ul>
                {stats.expiring.map((lot) => (
                  <li key={lot.id}>
                    {lot.item_name} at {lot.location_name}: {lot.quantity} {lot.unit}, expires {lot.expires_on}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default DashboardPage;
