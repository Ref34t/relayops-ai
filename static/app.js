const subtitle = document.querySelector("#subtitle");
const metrics = document.querySelector("#metrics");
const capabilities = document.querySelector("#capabilities");
const health = document.querySelector("#health");
const integrations = document.querySelector("#integrations");
const runs = document.querySelector("#runs");
const form = document.querySelector("#workflow-form");
const formStatus = document.querySelector("#form-status");

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
    fetch("/api/overview"),
    fetch("/api/health"),
    fetch("/api/integrations"),
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

  const response = await fetch("/api/workflows/execute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    formStatus.textContent = "The workflow request failed. Check the backend and try again.";
    return;
  }

  await loadOverview();
  formStatus.textContent = "Workflow created. Scroll updated to the latest runs.";
  document.querySelector("#demo").scrollIntoView({ behavior: "smooth", block: "start" });
});

loadOverview();
