import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const { setUser } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await login(email, password);
      setUser(user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Sign in</h2>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            style={styles.input}
          />

          <label style={styles.label}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            style={styles.input}
          />

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f5f5f5",
  },
  card: {
    background: "#fff",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 2px 12px rgba(0,0,0,0.1)",
    width: "100%",
    maxWidth: "400px",
  },
  title: {
    marginBottom: "1.5rem",
    fontSize: "1.5rem",
    fontWeight: 600,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "0.75rem",
  },
  label: {
    fontSize: "0.875rem",
    fontWeight: 500,
    color: "#333",
  },
  input: {
    padding: "0.6rem 0.75rem",
    border: "1px solid #ddd",
    borderRadius: "6px",
    fontSize: "1rem",
    outline: "none",
  },
  error: {
    color: "#c0392b",
    fontSize: "0.875rem",
    margin: 0,
  },
  button: {
    marginTop: "0.5rem",
    padding: "0.7rem",
    backgroundColor: "#01696f",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontSize: "1rem",
    cursor: "pointer",
    fontWeight: 600,
  },
};

export default LoginPage;