import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../api/auth";
import { ErrorText, Field, styles } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

function LoginPage() {
  const { setUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = creating ? await register(email, password) : await login(email, password);
      setUser(user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
          <div className="app-brand" style={{ padding: 0 }}>
            <img className="app-mark" src="/logo.svg" alt="" />
            <span>
              <strong>WorkPulse</strong>
              <span>Site operations</span>
            </span>
          </div>
          <button type="button" className="ghost-btn" onClick={toggleTheme}>
            {theme === "dark" ? "Light" : "Dark"}
          </button>
        </div>
        <div>
          <h1>{creating ? "Create account" : "Sign in"}</h1>
          <p className="lede">Manage crews, daily work, and site progress from one place.</p>
        </div>
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.85rem" }}>
          <Field label="Email">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={styles.input}
            />
          </Field>
          <Field label="Password">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={styles.input}
            />
          </Field>
          <ErrorText>{error}</ErrorText>
          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Please wait..." : creating ? "Create account" : "Sign in"}
          </button>
          <button
            type="button"
            className="login-switch"
            onClick={() => {
              setCreating((value) => !value);
              setError("");
            }}
          >
            {creating ? "Already have an account? Sign in" : "Need an account? Create one"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
