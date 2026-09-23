import { useState } from "react";
import { labPost } from "../api/labClient";

export default function Login({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await labPost<{ ok: boolean }>("/lab/login", { password });
      if (result.ok) {
        onSuccess();
      } else {
        setError("Incorrect password.");
      }
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div data-testid="page-lab-login">
      <h1>BenefitsWorld</h1>
      <h2>Lab Console</h2>
      <p className="muted">Researcher login.</p>
      <form onSubmit={onSubmit}>
        <label>
          Password{" "}
          <input
            type="password"
            data-testid="lab-login-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
        </label>{" "}
        <button type="submit" data-testid="lab-login-submit" disabled={submitting}>
          Log in
        </button>
      </form>
      {error && (
        <p style={{ color: "red" }} data-testid="lab-login-error">
          {error}
        </p>
      )}
    </div>
  );
}
