const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./frontend-tests",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure"
  },
  webServer: [
    {
      command: "python3 - <<'PY'\nfrom pathlib import Path\np = Path('data/e2e.db')\nif p.exists():\n    p.unlink()\nPY\nRELAYOPS_DB_PATH=data/e2e.db python3 -m uvicorn app.main:app --port 8123",
      port: 8123,
      reuseExistingServer: true,
      timeout: 120000
    },
    {
      command: "RELAYOPS_BACKEND_URL=http://127.0.0.1:8123 npm run dev -- --port 3100",
      cwd: "web",
      port: 3100,
      reuseExistingServer: true,
      timeout: 120000
    }
  ]
});
