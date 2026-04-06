import { useAuth } from "../context/AuthContext";
import { logout } from "../api/auth";
import { useNavigate } from "react-router-dom";

function DashboardPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    setUser(null);
    navigate("/login");
  }

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Welcome, {user?.email}</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}

export default DashboardPage;