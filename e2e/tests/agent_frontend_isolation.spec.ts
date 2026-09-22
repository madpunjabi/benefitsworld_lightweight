import { execSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

const FRONTEND_AGENT_DIR = path.resolve(__dirname, "../../frontend-agent");
const DIST_DIR = path.join(FRONTEND_AGENT_DIR, "dist");

const FORBIDDEN_PATTERNS = [
  /5174/,
  /localhost:5174/,
  /\/lab\//,
  /X-Lab-Token/i,
  /lab-token/i,
  /LabConsole/,
  /frontend-lab/,
];

test.beforeAll(() => {
  if (!existsSync(DIST_DIR)) {
    execSync("npm run build", { cwd: FRONTEND_AGENT_DIR, stdio: "inherit" });
  }
});

test("frontend-agent production bundle contains no lab references", () => {
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

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    for (const pattern of FORBIDDEN_PATTERNS) {
      expect(content, `${path.relative(DIST_DIR, file)} matched ${pattern}`).not.toMatch(pattern);
    }
  }
});
