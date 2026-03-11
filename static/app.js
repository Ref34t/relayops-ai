const subtitle = document.querySelector("#subtitle");
const metrics = document.querySelector("#metrics");
const capabilities = document.querySelector("#capabilities");
const health = document.querySelector("#health");
const integrations = document.querySelector("#integrations");
const runs = document.querySelector("#runs");
const form = document.querySelector("#workflow-form");
const formStatus = document.querySelector("#form-status");
const authForm = document.querySelector("#auth-form");
const authStatus = document.querySelector("#auth-status");
const apiKeyInput = document.querySelector("#api-key-input");
const workspaceName = document.querySelector("#workspace-name");
const workspaceMode = document.querySelector("#workspace-mode");

const API_KEY_STORAGE = "relayops_api_key";

function authHeaders() {
  const apiKey = localStorage.getItem(API_KEY_STORAGE);
  return apiKey ? { "X-RelayOps-Api-Key": apiKey } : {};
}

function clearStoredKey() {
  localStorage.removeItem(API_KEY_STORAGE);
}

async function loadAccount() {
  let response = await fetch("/api/account", { headers: authHeaders() });
  if (response.status === 401) {
    clearStoredKey();
    response = await fetch("/api/account");
  }
  if (!response.ok) {
    workspaceName.textContent = "Unauthorized";
    workspaceMode.textContent = "Invalid key";
    authStatus.textContent = "The stored API key is invalid. Re-enter a valid workspace key.";
    return;
  }
  const data = await response.json();
  workspaceName.textContent = data.account.name;
  workspaceMode.textContent = data.account.api_key === "relayops-demo-key" ? "Demo workspace" : "Custom key";
  if (!apiKeyInput.value) {
    apiKeyInput.value = localStorage.getItem(API_KEY_STORAGE) ?? data.account.api_key;
  }
}

function renderMetrics(items) {
  metrics.innerHTML = items
    .map(
      (item) => `
        <article class="metric-card">
          <p class="metric-label">${item.label}</p>
          <strong class="metric-value">${item.value}</strong>
          <p class="metric-detail">${item.detail}</p>
        </article>
      `,
    )
    .join("");
}

function renderCapabilities(items) {
  capabilities.innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function renderHealth(item) {
  health.innerHTML = `
    <article class="metric-card">
      <p class="metric-label">System Status</p>
      <strong class="metric-value">${item.status}</strong>
      <p class="metric-detail">SQLite-backed workflow store connected at runtime.</p>
    </article>
    <article class="metric-card">
      <p class="metric-label">Persisted Runs</p>
      <strong class="metric-value">${item.total_runs}</strong>
      <p class="metric-detail">${item.completed_runs} completed runs available for review.</p>
    </article>
    <article class="metric-card">
      <p class="metric-label">Sync Targets</p>
      <strong class="metric-value">${item.sync_targets}</strong>
      <p class="metric-detail">Tracked downstream sync operations across connected systems.</p>
    </article>
  `;
}

function renderIntegrations(items) {
  integrations.innerHTML = items
    .map(
      (item) => `
        <article class="metric-card">
          <p class="metric-label">${item.provider}</p>
          <strong class="metric-value integration-mode">${item.mode}</strong>
          <p class="metric-detail">${item.detail}</p>
          <p class="settings-action">${item.action ?? ""}</p>
        </article>
      `,
    )
    .join("");
}

function renderRuns(items) {
  runs.innerHTML = items
    .map(
      (run) => `
        <article class="run-card">
          <div class="run-score">${run.score}</div>
          <div class="run-meta">
            <span>${run.normalized.company}</span>
            <span>${run.source}</span>
          </div>
          <h3>${run.normalized.contact_name}</h3>
          <p>${run.summary}</p>
          <div class="mini-meta">
            <span>${run.normalized.urgency} urgency</span>
            <span>${run.status}</span>
            <span>${run.normalized.monthly_revenue}</span>
          </div>
          <div class="ai-panel">
            <p class="ops-heading">AI analysis</p>
            <h4>${run.ai_analysis.executive_title}</h4>
            <p class="ai-risk">Risk: ${run.ai_analysis.risk_level}</p>
            <ul class="ops-list">
              ${run.ai_analysis.highlights.map((item) => `<li>${item}</li>`).join("")}
            </ul>
            <p class="ops-heading">Next steps</p>
            <ul class="ops-list">
              ${run.ai_analysis.next_steps.map((item) => `<li>${item}</li>`).join("")}
            </ul>
            <p class="ops-heading">Automation opportunities</p>
            <ul class="ops-list">
              ${run.ai_analysis.automation_opportunities.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </div>
          <div class="tag-row">
            ${run.normalized.requested_systems.map((tag) => `<span class="tag">${tag}</span>`).join("")}
          </div>
          <div class="ops-stack">
            <div>
              <p class="ops-heading">Audit trail</p>
              <ul class="ops-list">
                ${run.audit_events.map((event) => `<li>${event.stage}: ${event.detail}</li>`).join("")}
              </ul>
            </div>
            <div>
              <p class="ops-heading">Sync results</p>
              <ul class="ops-list">
                ${run.sync_results.map((sync) => `<li>${sync.target}: ${sync.status} in ${sync.latency_ms}ms</li>`).join("")}
              </ul>
            </div>
          </div>
        </article>
      `,
    )
    .join("");
}

async function loadOverview() {
  let [overviewResponse, healthResponse, integrationResponse] = await Promise.all([
    fetch("/api/overview", { headers: authHeaders() }),
    fetch("/api/health", { headers: authHeaders() }),
    fetch("/api/integrations", { headers: authHeaders() }),
  ]);

  if ([overviewResponse, healthResponse, integrationResponse].some((response) => response.status === 401)) {
    clearStoredKey();
    [overviewResponse, healthResponse, integrationResponse] = await Promise.all([
      fetch("/api/overview"),
      fetch("/api/health"),
      fetch("/api/integrations"),
    ]);
  }

  if (!overviewResponse.ok || !healthResponse.ok || !integrationResponse.ok) {
    subtitle.textContent = "The backend is unavailable. Start the local API and reload.";
    return;
  }
  const data = await overviewResponse.json();
  const healthData = await healthResponse.json();
  const integrationData = await integrationResponse.json();

  subtitle.textContent = data.subtitle;
  renderMetrics(data.metrics);
  renderCapabilities(data.capabilities);
  renderHealth(healthData);
  renderIntegrations(integrationData.items);
  renderRuns(data.recent_runs);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formStatus.textContent = "Executing workflow...";

  const formData = new FormData(form);
  const payload = {
    source: formData.get("source"),
    company: formData.get("company"),
    contact_name: formData.get("contact_name"),
    email: formData.get("email"),
    requested_systems: String(formData.get("requested_systems"))
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
    pain_points: String(formData.get("pain_points"))
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
    monthly_revenue: formData.get("monthly_revenue"),
    urgency: formData.get("urgency"),
    notes: formData.get("notes"),
  };

  const response = await fetch("/api/workflows/execute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredKey();
      authStatus.textContent = "Stored workspace key was invalid. Reverted to the demo workspace.";
      await loadAccount();
      await loadOverview();
      formStatus.textContent = "Retry with a valid workspace key or use the demo workspace.";
      return;
    }
    formStatus.textContent = "The workflow request failed. Check the backend and try again.";
    return;
  }

  await loadOverview();
  formStatus.textContent = "Workflow created. Scroll updated to the latest runs.";
  document.querySelector("#demo").scrollIntoView({ behavior: "smooth", block: "start" });
});

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = apiKeyInput.value.trim();
  if (!value) {
    authStatus.textContent = "Enter a workspace API key.";
    return;
  }
  localStorage.setItem(API_KEY_STORAGE, value);
  authStatus.textContent = "Workspace key saved. Reloading workspace context...";
  await loadAccount();
  await loadOverview();
  authStatus.textContent = "Workspace context updated.";
});

loadAccount();
loadOverview();
