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
const loginForm = document.querySelector("#login-form");
const loginStatus = document.querySelector("#login-status");
const registerForm = document.querySelector("#register-form");
const registerStatus = document.querySelector("#register-status");
const logoutButton = document.querySelector("#logout-button");

const API_KEY_STORAGE = "relayops_api_key";

function authHeaders() {
  const apiKey = localStorage.getItem(API_KEY_STORAGE);
  return apiKey ? { "X-RelayOps-Api-Key": apiKey } : {};
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...authHeaders(),
    },
  });

  if (response.status === 401 && localStorage.getItem(API_KEY_STORAGE)) {
    localStorage.removeItem(API_KEY_STORAGE);
    return fetch(url, { credentials: "same-origin", ...options });
  }
  return response;
}

async function loadAccount() {
  const response = await apiFetch("/api/account");
  if (!response.ok) {
    workspaceName.textContent = "Unavailable";
    workspaceMode.textContent = "Error";
    return;
  }
  const data = await response.json();
  workspaceName.textContent = data.account.name;
  const modeMap = {
    session: "Session workspace",
    api_key: "API key",
    demo: "Demo workspace",
  };
  workspaceMode.textContent = modeMap[data.auth_mode] ?? data.auth_mode;
  if (!apiKeyInput.value) {
    apiKeyInput.value = localStorage.getItem(API_KEY_STORAGE) ?? "";
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
      <p class="metric-detail">${item.completed_runs} completed or degraded runs available for review.</p>
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
  const [overviewResponse, healthResponse, integrationResponse] = await Promise.all([
    apiFetch("/api/overview"),
    apiFetch("/api/health"),
    apiFetch("/api/integrations"),
  ]);

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

  const response = await apiFetch("/api/workflows/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    formStatus.textContent = response.status === 429 ? "Rate limit hit. Wait a minute and try again." : "The workflow request failed. Check the backend and try again.";
    return;
  }

  await loadAccount();
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
  authStatus.textContent = "API key saved. Reloading workspace context...";
  await loadAccount();
  await loadOverview();
  authStatus.textContent = "Workspace context updated.";
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginStatus.textContent = "Creating session...";
  const payload = Object.fromEntries(new FormData(loginForm).entries());
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    loginStatus.textContent = "Sign-in failed. Check your credentials.";
    return;
  }
  localStorage.removeItem(API_KEY_STORAGE);
  loginStatus.textContent = "Signed in.";
  await loadAccount();
  await loadOverview();
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  registerStatus.textContent = "Creating workspace...";
  const payload = Object.fromEntries(new FormData(registerForm).entries());
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    registerStatus.textContent = response.status === 409 ? "That email already has a workspace." : "Workspace creation failed.";
    return;
  }
  localStorage.removeItem(API_KEY_STORAGE);
  registerForm.reset();
  registerStatus.textContent = "Workspace created and signed in.";
  await loadAccount();
  await loadOverview();
});

logoutButton.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  localStorage.removeItem(API_KEY_STORAGE);
  authStatus.textContent = "Session cleared. Back to the demo workspace.";
  await loadAccount();
  await loadOverview();
});

loadAccount();
loadOverview();
