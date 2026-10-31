import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Layout from "./components/Layout";
import CompanyPage from "./pages/CompanyPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import StockPage from "./pages/StockPage";
import TeamsPage from "./pages/TeamsPage";
import WorkersPage from "./pages/WorkersPage";
import WorkplacePage from "./pages/WorkplacePage";
import WorkplacesPage from "./pages/WorkplacesPage";
import WorkTypesPage from "./pages/WorkTypesPage";
import ReportsPage from "./pages/ReportsPage";
import ProtectedRoute from "./routes/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/company" element={<CompanyPage />} />
            <Route path="/teams" element={<TeamsPage />} />
            <Route path="/workers" element={<WorkersPage />} />
            <Route path="/work-types" element={<WorkTypesPage />} />
            <Route path="/contracts" element={<WorkplacesPage />} />
            <Route path="/contracts/:id" element={<WorkplacePage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/stock" element={<StockPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
