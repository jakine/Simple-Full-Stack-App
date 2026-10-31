import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const linkStyle = ({ isActive }) => ({
  color: isActive ? "#01696f" : "#333",
  fontWeight: isActive ? 700 : 500,
  textDecoration: "none",
});

function Layout() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const company = user?.active_company;
  const location = useLocation();
  const needsCompany = location.pathname !== "/company" && location.pathname !== "/dashboard";

  async function handleLogout() {
    await logout();
    setUser(null);
    navigate("/login");
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f4f6f6" }}>
      <header
        style={{
          background: "#fff",
          borderBottom: "1px solid #e6e6e6",
          padding: "0.9rem 1.5rem",
          display: "flex",
          gap: "1.25rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <Link to="/dashboard" style={{ color: "#01696f", fontWeight: 700, textDecoration: "none" }}>
          Workforce
        </Link>
        <span style={{ color: "#555" }}>
          {company ? `${company.name} · ${company.role}` : "No company selected"}
        </span>
        <nav style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <NavLink to="/company" style={linkStyle}>
            Company
          </NavLink>
          {company && (
            <>
              <NavLink to="/teams" style={linkStyle}>
                Teams
              </NavLink>
              <NavLink to="/workers" style={linkStyle}>
                Workers
              </NavLink>
              <NavLink to="/work-types" style={linkStyle}>
                Work types
              </NavLink>
              <NavLink to="/contracts" style={linkStyle}>
                Contracts
              </NavLink>
              <NavLink to="/reports" style={linkStyle}>
                Reports
              </NavLink>
              <NavLink to="/stock" style={linkStyle}>
                Stock
              </NavLink>
            </>
          )}
        </nav>
        <button
          onClick={handleLogout}
          style={{
            marginLeft: "auto",
            border: "1px solid #ddd",
            background: "#fff",
            borderRadius: "6px",
            padding: "0.4rem 0.7rem",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </header>
      <main style={{ padding: "1.5rem", maxWidth: "1100px" }}>
        {!company && needsCompany ? <Navigate to="/company" replace /> : <Outlet />}
      </main>
    </div>
  );
}

export default Layout;
