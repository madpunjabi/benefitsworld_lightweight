import { Link, Navigate, Route, Routes } from "react-router-dom";
import AgentStatus from "./pages/AgentStatus";
import Calendar from "./pages/Calendar";
import Files from "./pages/Files";
import Inbox from "./pages/Inbox";
import Policy from "./pages/Policy";
import Portal from "./pages/Portal";

const NAV = [
  ["/portal", "Case Portal"],
  ["/inbox", "Inbox"],
  ["/files", "My Files"],
  ["/calendar", "Calendar"],
  ["/policy", "Policy Library"],
  ["/agent", "Case Status"],
] as const;

export default function App() {
  return (
    <div>
      <header className="site-header">
        <h1>Alameda County Human Services — CalFresh Case Portal</h1>
      </header>
      <nav className="site-nav">
        {NAV.map(([path, label]) => (
          <Link key={path} to={path}>
            {label}
          </Link>
        ))}
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/portal" replace />} />
          <Route path="/portal" element={<Portal />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/files" element={<Files />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/policy" element={<Policy />} />
          <Route path="/agent" element={<AgentStatus />} />
        </Routes>
      </main>
    </div>
  );
}
