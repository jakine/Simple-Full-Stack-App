export const styles = {
  page: { display: "grid", gap: "1.25rem" },
  card: {
    background: "#fff",
    border: "1px solid #e6e6e6",
    borderRadius: "8px",
    padding: "1rem 1.25rem",
  },
  row: { display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "end" },
  field: { display: "flex", flexDirection: "column", gap: "0.35rem", minWidth: "10rem" },
  label: { fontSize: "0.8rem", fontWeight: 600, color: "#333" },
  input: {
    padding: "0.5rem 0.65rem",
    border: "1px solid #ddd",
    borderRadius: "6px",
    fontSize: "0.95rem",
  },
  button: {
    padding: "0.55rem 0.9rem",
    backgroundColor: "#01696f",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontWeight: 600,
    cursor: "pointer",
  },
  quiet: {
    padding: "0.45rem 0.7rem",
    background: "#fff",
    color: "#01696f",
    border: "1px solid #01696f",
    borderRadius: "6px",
    cursor: "pointer",
  },
  danger: {
    padding: "0.35rem 0.6rem",
    background: "#fff",
    color: "#c0392b",
    border: "1px solid #e5c5c1",
    borderRadius: "6px",
    cursor: "pointer",
  },
  error: { color: "#c0392b", margin: 0 },
  table: { width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" },
  th: { textAlign: "left", padding: "0.45rem", borderBottom: "1px solid #ddd", color: "#555" },
  td: { padding: "0.45rem", borderBottom: "1px solid #f0f0f0", verticalAlign: "top" },
  stats: { display: "flex", gap: "1rem", flexWrap: "wrap" },
  stat: {
    background: "#f3f7f7",
    borderRadius: "8px",
    padding: "0.75rem 1rem",
    minWidth: "8rem",
  },
};

export function Field({ label, children }) {
  return (
    <label style={styles.field}>
      <span style={styles.label}>{label}</span>
      {children}
    </label>
  );
}

export function ErrorText({ children }) {
  if (!children) return null;
  return <p style={styles.error}>{children}</p>;
}
