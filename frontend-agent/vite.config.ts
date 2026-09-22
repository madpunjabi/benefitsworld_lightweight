import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Fixed port, no proxy to the lab origin or lab API — this app only ever
// talks to the public backend router (see src/api/client.ts). Isolation
// from the Lab Console is a build-time property: nothing in this package
// imports, links to, or knows about frontend-lab.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
  preview: { port: 5173, strictPort: true },
});
