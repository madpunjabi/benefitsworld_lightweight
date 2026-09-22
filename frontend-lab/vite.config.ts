import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Completely separate package/build/port from frontend-agent. Researcher-
// only; the benchmark agent's browser never receives this origin.
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, strictPort: true },
  preview: { port: 5174, strictPort: true },
});
