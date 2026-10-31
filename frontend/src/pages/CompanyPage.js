import { useEffect, useState } from "react";
import { api, apiList } from "../api/client";
import { getMe } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { ErrorText, Field, styles } from "../components/ui";

function CompanyPage() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [members, setMembers] = useState([]);
  const [error, setError] = useState("");

  const company = user?.active_company;

  async function refreshUser() {
    setUser(await getMe());
  }

  useEffect(() => {
    if (!company) {
      setMembers([]);
      return;
    }
    apiList("/companies/members/")
      .then(setMembers)
      .catch((err) => setError(err.message));
  }, [company]);

  async function createCompany(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/companies/", { method: "POST", body: { name } });
      setName("");
      await refreshUser();
    } catch (err) {
      setError(err.message);
    }
  }

  async function switchCompany(companyId) {
    setError("");
    try {
      await api("/companies/switch/", { method: "POST", body: { company_id: companyId } });
      await refreshUser();
    } catch (err) {
      setError(err.message);
    }
  }

  async function invite(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/companies/members/", { method: "POST", body: { email, password } });
      setEmail("");
      setPassword("");
      setMembers(await apiList("/companies/members/"));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={{ margin: 0 }}>Company</h1>
      <ErrorText>{error}</ErrorText>

      <form onSubmit={createCompany} style={styles.card}>
        <h2 style={{ marginTop: 0 }}>New company</h2>
        <div style={styles.row}>
          <Field label="Name">
            <input style={styles.input} value={name} onChange={(e) => setName(e.target.value)} required />
          </Field>
          <button style={styles.button} type="submit">
            Create
          </button>
        </div>
      </form>

      <div style={styles.card}>
        <h2 style={{ marginTop: 0 }}>Your companies</h2>
        {(user?.companies || []).length === 0 ? (
          <p>You do not belong to a company yet.</p>
        ) : (
          <ul>
            {(user.companies || []).map((item) => (
              <li key={item.id} style={{ marginBottom: "0.5rem" }}>
                {item.name} ({item.role})
                {company?.id !== item.id && (
                  <button style={{ ...styles.quiet, marginLeft: "0.75rem" }} type="button" onClick={() => switchCompany(item.id)}>
                    Switch
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {company?.role === "owner" && (
        <form onSubmit={invite} style={styles.card}>
          <h2 style={{ marginTop: 0 }}>Invite a manager</h2>
          <div style={styles.row}>
            <Field label="Email">
              <input style={styles.input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </Field>
            <Field label="Password for a new account">
              <input style={styles.input} type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <button style={styles.button} type="submit">
              Invite
            </button>
          </div>
        </form>
      )}

      {company && (
        <div style={styles.card}>
          <h2 style={{ marginTop: 0 }}>People</h2>
          <ul>
            {members.map((member) => (
              <li key={member.id}>
                {member.email} · {member.role}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default CompanyPage;
