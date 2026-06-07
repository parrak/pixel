const metricsNode = document.getElementById("demoMetrics");
const organizationList = document.getElementById("organizationList");
const mondayPanel = document.getElementById("mondayPanel");
const roleList = document.getElementById("roleList");
const recommendationPanel = document.getElementById("recommendationPanel");
const decisionPanel = document.getElementById("decisionPanel");
const outcomePanel = document.getElementById("outcomePanel");
const loadButton = document.getElementById("loadDemo");
const runSimulator = document.getElementById("runSimulator");
const simulatorPanel = document.getElementById("simulatorPanel");

let portfolioState = null;

function formatMoney(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `$${value}`;
}

async function fetchPortfolio() {
  const response = await fetch("/api/summary");
  if (!response.ok) {
    throw new Error("Failed to load synthetic portfolio");
  }
  return response.json();
}

async function fetchAcquisition(params) {
  const query = new URLSearchParams(params);
  const response = await fetch(`/api/acquisition?${query.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to load acquisition simulation");
  }
  return response.json();
}

if (loadButton) {
  loadButton.addEventListener("click", async () => {
    loadButton.disabled = true;
    loadButton.textContent = "Loading...";
    try {
      portfolioState = await fetchPortfolio();
      renderMetrics(portfolioState.portfolio_snapshot.holdco_dashboard);
      renderLeadershipFocus(portfolioState.portfolio_snapshot.holdco_dashboard, portfolioState.portfolio_snapshot.executive_operating_review);
      renderOrganizations(portfolioState.portfolio_snapshot);
    } catch (error) {
      mondayPanel.innerHTML = `<p>${error.message}</p>`;
    } finally {
      loadButton.disabled = false;
      loadButton.textContent = "Reload HoldCo";
    }
  });
}

if (runSimulator) {
  runSimulator.addEventListener("click", async () => {
    const specialty = document.getElementById("specialtySelect").value;
    const headcount = Number(document.getElementById("headcountInput").value);
    const workflowMaturity = document.getElementById("maturitySelect").value;
    runSimulator.disabled = true;
    runSimulator.textContent = "Generating...";
    try {
      const simulation = await fetchAcquisition({
        specialty,
        headcount: String(headcount),
        workflow_maturity: workflowMaturity,
      });
      renderSimulator(simulation);
    } catch (error) {
      simulatorPanel.innerHTML = `<p>${error.message}</p>`;
    } finally {
      runSimulator.disabled = false;
      runSimulator.textContent = "Generate Integration Plan";
    }
  });
}

function renderMetrics(holdcoDashboard) {
  metricsNode.innerHTML = `
    <div><strong>${formatMoney(holdcoDashboard.portfolio_revenue)}</strong><br/>Portfolio revenue</div>
    <div><strong>${formatMoney(holdcoDashboard.portfolio_ebitda)}</strong><br/>Portfolio EBITDA</div>
    <div><strong>${formatMoney(holdcoDashboard.revenue_at_risk)}</strong><br/>Revenue at risk</div>
    <div><strong>${holdcoDashboard.value_creation_progress.progress_pct}%</strong><br/>Value creation progress</div>
  `;
}

function renderLeadershipFocus(holdcoDashboard, executiveReview) {
  mondayPanel.innerHTML = `
    <strong>What work should get done next</strong>
    <ul>${holdcoDashboard.focus_today.map((line) => `<li>${line}</li>`).join("")}</ul>
    <p><strong>Workflow pressure:</strong> ${holdcoDashboard.critical_bottlenecks.join(" | ")}</p>
  `;
}

function renderOrganizations(portfolio) {
  organizationList.innerHTML = "";
  portfolio.organization_summaries.forEach((organization, index) => {
    const item = document.createElement("button");
    item.className = `queue-item${index === 0 ? " is-active" : ""}`;
    item.innerHTML = `
      <strong>${organization.name}</strong>
      <p>${organization.thesis}</p>
      <p>Revenue at risk: ${formatMoney(organization.revenue_at_risk)} · Open work: ${organization.open_work}</p>
    `;
    item.addEventListener("click", () => {
      document.querySelectorAll("#organizationList .queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderOrganization(organization, portfolio);
    });
    organizationList.appendChild(item);
  });
  renderOrganization(portfolio.organization_summaries[0], portfolio);
}

function renderOrganization(organization, portfolio) {
  const roleViews = (portfolio.organization_role_views.find((item) => item.organization_id === organization.organization_id) || { roles: [] }).roles;
  roleList.innerHTML = "";
  roleViews.forEach((roleEntry, index) => {
    const item = document.createElement("button");
    item.className = `queue-item${index === 0 ? " is-active" : ""}`;
    item.innerHTML = `
      <strong>${roleEntry.label}</strong>
      <p>${roleEntry.queue_size} queued item(s)</p>
      <p>Revenue at risk: ${formatMoney(roleEntry.revenue_at_risk)}</p>
    `;
    item.addEventListener("click", () => {
      document.querySelectorAll("#roleList .queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderRole(roleEntry, organization, portfolio);
    });
    roleList.appendChild(item);
  });
  if (roleViews.length) {
    renderRole(roleViews[0], organization, portfolio);
  }
}

function renderRole(roleEntry, organization, portfolio) {
  const workObject = portfolio.work_objects.find((item) =>
    item.organization_id === organization.organization_id && item.owner_role === roleEntry.role
  ) || portfolio.work_objects.find((item) => item.organization_id === organization.organization_id);
  const pattern = portfolio.decision_intelligence.patterns.find((item) => item.organization === organization.name);
  recommendationPanel.innerHTML = `
    <strong>${workObject.title}</strong>
    <p><strong>Type:</strong> ${workObject.work_object_type}</p>
    <p><strong>Financial impact:</strong> ${formatMoney(workObject.financial_impact)}</p>
    <p><strong>Status:</strong> ${workObject.status} / ${workObject.workflow_status}</p>
    <p><strong>Recommendation:</strong> ${workObject.recommendations[0].title}</p>
  `;
  decisionPanel.innerHTML = workObject ? `
    <strong>${workObject.timeline[0].label}</strong>
    <p><strong>Evidence:</strong> ${workObject.evidence[0].title}</p>
    <p><strong>Detail:</strong> ${workObject.evidence[0].detail}</p>
    <p><strong>Next:</strong> ${workObject.timeline[workObject.timeline.length - 1].next_step}</p>
  ` : (pattern ? `
    <strong>${pattern.workflow}</strong>
    <p><strong>Playbook:</strong> ${pattern.playbook}</p>
    <p><strong>Decision owner:</strong> ${pattern.owner}</p>
    <p><strong>Outcome:</strong> ${pattern.outcome}</p>
  ` : "<p>No decision intelligence available.</p>");
  outcomePanel.innerHTML = `
    <strong>${organization.name} outcome</strong>
    <p><strong>Role queue:</strong> ${roleEntry.label}</p>
    <p><strong>Completed outcomes:</strong> ${roleEntry.completed_outcomes}</p>
    <p><strong>Financial result:</strong> ${formatMoney(roleEntry.financial_result)}</p>
    <p><strong>Institutional memory:</strong> ${workObject.institutional_memory[0].summary}</p>
  `;
}

function renderSimulator(simulation) {
  simulatorPanel.innerHTML = `
    <strong>${simulation.specialty} acquisition integration plan</strong>
    <p><strong>Current state:</strong> ${simulation.current_state_assessment.operating_model}</p>
    <p><strong>Technology gap:</strong> ${simulation.technology_gaps[0]}</p>
    <p><strong>Operational risk:</strong> ${simulation.operational_risks[0]}</p>
    <p><strong>90-day roadmap:</strong> ${simulation.ninety_day_roadmap.map((item) => `${item.window}: ${item.focus}`).join(" | ")}</p>
    <p><strong>Value creation:</strong> ${simulation.value_creation_opportunities.map((item) => `${item.initiative} (${formatMoney(item.expected_ebitda_impact)})`).join(" · ")}</p>
  `;
}
