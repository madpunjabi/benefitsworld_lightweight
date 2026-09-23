import { useEffect, useState } from "react";
import { labGet } from "./api/labClient";
import LabConsole from "./pages/LabConsole";
import Login from "./pages/Login";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(null); // null = still checking

  const checkSession = () => {
    labGet<{ authenticated: boolean }>("/lab/session")
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  };

  useEffect(() => {
    checkSession();
  }, []);

  if (authed === null) {
    return <p>Loading…</p>;
  }
  if (!authed) {
    return <Login onSuccess={() => setAuthed(true)} />;
  }
  return <LabConsole onLogout={() => setAuthed(false)} />;
}
