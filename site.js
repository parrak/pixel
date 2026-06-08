const metricsNode = document.getElementById("demoMetrics");
const roleList = document.getElementById("roleList");
const mondayPanel = document.getElementById("mondayPanel");
const queueList = document.getElementById("organizationList");
const graphPanel = document.getElementById("recommendationPanel");
const timelinePanel = document.getElementById("decisionPanel");
const actionPanel = document.getElementById("outcomePanel");

let portfolioState = null;
let selectedRole = "biller";

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

async function bootDemo() {
  try {
    portfolioState = await fetchPortfolio();
    renderOsLanding(portfolioState.portfolio_snapshot.operator_os_landing);
    renderRoles(portfolioState.portfolio_snapshot.persona_experiences);
    renderPersona(selectedRole);
  } catch (error) {
    mondayPanel.innerHTML = `<p>${error.message}</p>`;
  }
}

function renderOsLanding(landing) {
  metricsNode.innerHTML = `
    <div><strong>${formatMoney(landing.revenue_at_risk)}</strong><br/>Revenue at risk</div>
    <div><strong>${landing.open_work}</strong><br/>Open work</div>
    <div><strong>${landing.critical_appeals}</strong><br/>Critical appeals</div>
    <div><strong>${landing.authorizations_at_risk}</strong><br/>Authorizations at risk</div>
    <div><strong>${landing.coding_reviews_pending}</strong><br/>Coding reviews pending</div>
  `;
}

function renderRoles(personas) {
  roleList.innerHTML = "";
  Object.values(personas).forEach((persona) => {
    const item = document.createElement("button");
    item.className = `queue-item${persona.role === selectedRole ? " is-active" : ""}`;
    item.innerHTML = `
      <strong>${persona.label}</strong>
      <p>${persona.operator_question}</p>
      <p>${persona.navigation.join(" · ")}</p>
    `;
    item.addEventListener("click", () => {
      selectedRole = persona.role;
      document.querySelectorAll("#roleList .queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderPersona(selectedRole);
    });
    roleList.appendChild(item);
  });
}

function renderPersona(role) {
  const persona = portfolioState.portfolio_snapshot.persona_experiences[role];
  const workItem = persona.my_work[0] || persona.my_queue[0];
  mondayPanel.innerHTML = `
    <strong>${persona.label}</strong>
    <p><strong>Primary objects:</strong> ${persona.primary_objects.join(" → ")}</p>
    <p><strong>Navigation:</strong> ${persona.navigation.join(" · ")}</p>
    <p><strong>Open work:</strong> ${persona.metrics.open_work ?? "-"} · <strong>Blocked:</strong> ${persona.metrics.blocked_work ?? "-"}</p>
  `;
  renderQueue(persona, workItem);
  renderWorkObject(workItem, persona);
}

function renderQueue(persona, selectedItem) {
  queueList.innerHTML = "";
  persona.my_queue.forEach((item, index) => {
    const node = document.createElement("button");
    node.className = `queue-item${index === 0 ? " is-active" : ""}`;
    node.innerHTML = `
      <strong>${item.title}</strong>
      <p>${item.primary_object} · ${item.current_state} · ${formatMoney(item.expected_recovery)}</p>
      <p>Owner: ${item.owner} · Waiting on: ${item.dependency}</p>
    `;
    node.addEventListener("click", () => {
      document.querySelectorAll("#organizationList .queue-item").forEach((queueItem) => queueItem.classList.remove("is-active"));
      node.classList.add("is-active");
      renderWorkObject(item, persona);
    });
    queueList.appendChild(node);
  });
  if (!persona.my_queue.length) {
    queueList.innerHTML = "<p>No work assigned to this role in the synthetic dataset.</p>";
  } else {
    renderWorkObject(selectedItem || persona.my_queue[0], persona);
  }
}

function renderWorkObject(item, persona) {
  if (!item) {
    graphPanel.innerHTML = "<p>No work object available.</p>";
    timelinePanel.innerHTML = "<p>No timeline available.</p>";
    actionPanel.innerHTML = "<p>No recommended actions available.</p>";
    return;
  }
  const fullObject = portfolioState.portfolio_snapshot.work_objects.find((work) => work.work_object_id === item.work_object_id);
  const graph = fullObject.workflow_graph;
  graphPanel.innerHTML = `
    <strong>${item.title}</strong>
    <p><strong>Current State:</strong> ${graph.current_state}</p>
    <p><strong>Owner:</strong> ${graph.owner}</p>
    <p><strong>Waiting On:</strong> ${graph.waiting_on}</p>
    <p><strong>Days In State:</strong> ${graph.days_in_state}</p>
    <p><strong>Deadline:</strong> ${graph.deadline_days_remaining} days remaining</p>
    <p><strong>Expected Recovery:</strong> ${formatMoney(graph.expected_recovery)}</p>
    <div class="workflow-graph">${graph.stages.map(renderStage).join("")}</div>
  `;
  timelinePanel.innerHTML = `
    <strong>What happened</strong>
    <ul>${fullObject.timeline.map((event) => `<li><strong>${event.label}:</strong> ${event.detail}</li>`).join("")}</ul>
  `;
  actionPanel.innerHTML = `
    <strong>What happens next</strong>
    <ul>${persona.recommended_actions.map((action) => `<li><strong>${action.current_state} → ${action.next_state}:</strong> ${action.action}</li>`).join("")}</ul>
    <p><strong>Memory:</strong> ${fullObject.institutional_memory[0].summary}</p>
  `;
}

function renderStage(stage) {
  return `
    <div class="graph-node graph-${stage.status}">
      <strong>${stage.label}</strong>
      <span>${stage.owner}</span>
    </div>
  `;
}

bootDemo();
