import { createContext, useContext, useEffect, useState } from "react";
import { getMe } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    getMe()
      .then((data) => setUser(data))
      .catch(() => setUser(null));
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {user === undefined ? <p className="app-boot">Loading workspace…</p> : children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function useRole() {
  const { user } = useAuth();
  const role = user?.active_company?.role || "";
  return {
    role,
    isOwner: role === "owner",
    isLead: role === "team_lead",
    canManage: role === "owner" || role === "manager",
  };
}