const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./frontend-tests",
  use: {
    baseURL: "http://127.0.0.1:8123",
    trace: "retain-on-failure"
  },
  webServer: {
    command: "rm -f data/e2e.db && RELAYOPS_DB_PATH=data/e2e.db python3 -m uvicorn app.main:app --port 8123",
    port: 8123,
    reuseExistingServer: true,
    timeout: 120000
  }
});
