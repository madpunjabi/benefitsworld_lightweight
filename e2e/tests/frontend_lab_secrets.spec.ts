import { execSync } from "node:child_process";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { LAB_CONSOLE_PASSWORD, LAB_TOKEN } from "./helpers";

const FRONTEND_LAB_DIR = path.resolve(__dirname, "../../frontend-lab");
const DIST_DIR = path.join(FRONTEND_LAB_DIR, "dist");

test.beforeAll(() => {
  // Deliberately does NOT pass VITE_LAB_TOKEN (or any backend secret) into
  // the build environment — that's exactly the point being proven: the
  // production build must work, and be secret-free, without it.
  execSync("npm run build", { cwd: FRONTEND_LAB_DIR, stdio: "inherit" });
});

test("frontend-lab production bundle contains no embedded secrets", () => {
  const files: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else files.push(full);
    }
  };
  walk(DIST_DIR);

  expect(files.length).toBeGreaterThan(0);

  const forbidden = [
    LAB_TOKEN,
    LAB_CONSOLE_PASSWORD,
    "VITE_LAB_TOKEN",
    "X-Lab-Token",
    "dev-lab-token-benefitsworld-local-only",
    "dev-session-secret-benefitsworld-local-only",
  ];

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    for (const secret of forbidden) {
      expect(content, `${path.relative(DIST_DIR, file)} leaked '${secret}'`).not.toContain(secret);
    }
  }
});

test("frontend-lab source no longer references VITE_LAB_TOKEN at all", () => {
  const srcDir = path.join(FRONTEND_LAB_DIR, "src");
  const files: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else files.push(full);
    }
  };
  walk(srcDir);

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    expect(content, `${path.relative(srcDir, file)} still references VITE_LAB_TOKEN`).not.toContain(
      "VITE_LAB_TOKEN",
    );
  }
});
