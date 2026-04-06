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
      {user === undefined ? <p>Loading...</p> : children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}