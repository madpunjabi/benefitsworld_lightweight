import { Link, Navigate, Route, Routes } from "react-router-dom";
import AgentStatus from "./pages/AgentStatus";
import Calendar from "./pages/Calendar";
import Files from "./pages/Files";
import Inbox from "./pages/Inbox";
import Policy from "./pages/Policy";
import Portal from "./pages/Portal";

const NAV = [
  ["/portal", "Portal"],
  ["/inbox", "Inbox"],
  ["/files", "Files"],
  ["/calendar", "Calendar"],
  ["/policy", "Policy"],
  ["/agent", "Agent Status"],
] as const;

export default function App() {
  return (
    <div>
      <nav>
        {NAV.map(([path, label]) => (
          <Link key={path} to={path} style={{ marginRight: 12 }}>
            {label}
          </Link>
        ))}
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/portal" replace />} />
        <Route path="/portal" element={<Portal />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/files" element={<Files />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/policy" element={<Policy />} />
        <Route path="/agent" element={<AgentStatus />} />
      </Routes>
    </div>
  );
}
