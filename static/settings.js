const statusMessage = document.querySelector("#settings-status");
const container = document.querySelector("#settings-integrations");
const runChecksButton = document.querySelector("#run-checks");

function renderCards(items) {
  container.innerHTML = items
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

async function loadSettings() {
  const response = await fetch("/api/integrations");
  if (!response.ok) {
    statusMessage.textContent = "Could not load integration status.";
    return;
  }
  const data = await response.json();
  statusMessage.textContent = "Current connector status based on local environment and latest runtime diagnostics.";
  renderCards(data.items);
}

runChecksButton.addEventListener("click", async () => {
  statusMessage.textContent = "Running connector checks...";
  const response = await fetch("/api/integrations/check", { method: "POST" });
  if (!response.ok) {
    statusMessage.textContent = "Connector checks failed.";
    return;
  }
  const data = await response.json();
  statusMessage.textContent = "Connector checks completed. Review any misconfigured providers below.";
  renderCards(data.items);
});

loadSettings();
