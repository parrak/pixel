const metricsNode = document.getElementById("demoMetrics");
const roleList = document.getElementById("roleList");
const mondayPanel = document.getElementById("mondayPanel");
const queueList = document.getElementById("organizationList");
const graphPanel = document.getElementById("recommendationPanel");
const timelinePanel = document.getElementById("decisionPanel");
const actionPanel = document.getElementById("outcomePanel");

let portfolioState = null;
let selectedRole = "biller";

const fallbackPortfolio = {
  portfolio_snapshot: {
    operator_os_landing: {
      revenue_at_risk: "2500000.00",
      open_work: 126,
      critical_appeals: 14,
      authorizations_at_risk: 8,
      coding_reviews_pending: 22,
    },
    persona_experiences: {
      coder: {
        role: "coder",
        label: "Coding Specialist",
        operator_question: "Am I coding this encounter correctly?",
        primary_objects: ["Patient", "Encounter", "Procedure", "Documentation", "Coding Review", "Charge Capture"],
        navigation: ["My Reviews", "Documentation Gaps", "Coding Queue", "Procedure Explorer", "Completed Reviews", "Knowledge Base"],
        metrics: { open_work: 22, blocked_work: 4 },
        my_work: [
          {
            work_object_id: "WO-FILE-CODING-001",
            title: "Arthroscopy encounter coding review",
            primary_object: "Encounter",
            current_state: "Coding Review",
            expected_recovery: "1800.00",
            owner: "Coding Specialist",
            dependency: "Waiting on Coding Review",
          },
        ],
        my_queue: [],
        recommended_actions: [
          {
            current_state: "Coding Review",
            next_state: "Charge Capture",
            action: "Validate documentation supports coded procedure before claim submission.",
          },
        ],
      },
      denial_specialist: {
        role: "denial_specialist",
        label: "Denial Specialist",
        operator_question: "Which denials can I recover today?",
        primary_objects: ["Claim", "Denial", "Appeal", "Evidence"],
        navigation: ["My Denials", "Appeals", "Evidence", "Payer Playbooks", "Completed Recoveries"],
        metrics: { open_work: 31, blocked_work: 9 },
        my_work: [
          {
            work_object_id: "WO-FILE-DENIAL-001",
            title: "United medical necessity appeal",
            primary_object: "Denial",
            current_state: "Appeal",
            expected_recovery: "4250.00",
            owner: "Sarah Chen",
            dependency: "Waiting on Payer",
          },
        ],
        my_queue: [],
        recommended_actions: [
          {
            current_state: "Appeal",
            next_state: "Resolution",
            action: "Track payer response and escalate if no acknowledgement before deadline.",
          },
        ],
      },
      biller: {
        role: "biller",
        label: "AR Specialist",
        operator_question: "Which balances can I recover or escalate?",
        primary_objects: ["Account", "Claim", "Balance", "Recovery Workflow"],
        navigation: ["My AR Queue", "Escalations", "High-Dollar Accounts", "Underpayments", "Completed Recoveries"],
        metrics: { open_work: 47, blocked_work: 11 },
        my_work: [
          {
            work_object_id: "WO-FILE-AR-001",
            title: "90+ day no-payment follow-up",
            primary_object: "Account",
            current_state: "Recovery Workflow",
            expected_recovery: "12500.00",
            owner: "Daniel Ortiz",
            dependency: "Waiting on Payer",
          },
        ],
        my_queue: [],
        recommended_actions: [
          {
            current_state: "Recovery Workflow",
            next_state: "Resolution",
            action: "Call payer, document reference number, and escalate if response is not committed today.",
          },
        ],
      },
      auth_specialist: {
        role: "auth_specialist",
        label: "Authorization Specialist",
        operator_question: "Which scheduled procedures are missing authorization work?",
        primary_objects: ["Scheduled Procedure", "Authorization", "Requirements"],
        navigation: ["Pending Auths", "Missing Requirements", "Expiring Auths", "Escalations"],
        metrics: { open_work: 8, blocked_work: 3 },
        my_work: [
          {
            work_object_id: "WO-FILE-AUTH-001",
            title: "Missing authorization before scheduled case",
            primary_object: "Scheduled Procedure",
            current_state: "Authorization",
            expected_recovery: "6200.00",
            owner: "Authorization Specialist",
            dependency: "Waiting on Authorization",
          },
        ],
        my_queue: [],
        recommended_actions: [
          {
            current_state: "Authorization",
            next_state: "Procedure",
            action: "Confirm payer requirements and coordinate missing authorization before date of service.",
          },
        ],
      },
      manager: {
        role: "manager",
        label: "Manager",
        operator_question: "Where should I intervene to unblock teams?",
        primary_objects: ["Teams", "Queues", "Capacity", "Productivity"],
        navigation: ["Operations", "Assignments", "Escalations", "Blockers", "Team Performance"],
        metrics: { open_work: 126, blocked_work: 27 },
        my_work: [],
        my_queue: [],
        recommended_actions: [],
      },
      vp_revenue_cycle: {
        role: "vp_revenue_cycle",
        label: "VP Revenue Cycle",
        operator_question: "Which operational bottlenecks are putting revenue at risk?",
        primary_objects: ["Revenue", "Risk", "Operational Bottlenecks"],
        navigation: ["Operational Health", "Revenue At Risk", "Payer Performance", "Interventions"],
        metrics: { open_work: 126, blocked_work: 27 },
        my_work: [],
        my_queue: [],
        recommended_actions: [],
      },
    },
    work_objects: [],
  },
};

fallbackPortfolio.portfolio_snapshot.persona_experiences.coder.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.coder.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.denial_specialist.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.denial_specialist.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.biller.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.biller.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.auth_specialist.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.auth_specialist.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.manager.my_work = fallbackPortfolio.portfolio_snapshot.persona_experiences.biller.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.manager.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.biller.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.manager.recommended_actions = fallbackPortfolio.portfolio_snapshot.persona_experiences.biller.recommended_actions;
fallbackPortfolio.portfolio_snapshot.persona_experiences.vp_revenue_cycle.my_work = fallbackPortfolio.portfolio_snapshot.persona_experiences.denial_specialist.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.vp_revenue_cycle.my_queue = fallbackPortfolio.portfolio_snapshot.persona_experiences.denial_specialist.my_work;
fallbackPortfolio.portfolio_snapshot.persona_experiences.vp_revenue_cycle.recommended_actions = fallbackPortfolio.portfolio_snapshot.persona_experiences.denial_specialist.recommended_actions;
fallbackPortfolio.portfolio_snapshot.work_objects = Object.values(fallbackPortfolio.portfolio_snapshot.persona_experiences)
  .flatMap((persona) => persona.my_work)
  .filter((item, index, items) => items.findIndex((candidate) => candidate.work_object_id === item.work_object_id) === index)
  .map((item) => ({
    work_object_id: item.work_object_id,
    title: item.title,
    timeline: [
      { label: "Claim Submitted", detail: "Claim entered the workflow system of record." },
      { label: "Work Assigned", detail: `${item.title} assigned to ${item.owner}.` },
      { label: "Evidence Generated", detail: "Citron assembled evidence and next-step work product." },
    ],
    institutional_memory: [{ summary: "Local file demo memory: decisions and outcomes persist with the work object." }],
    workflow_graph: {
      current_state: item.current_state,
      owner: item.owner,
      waiting_on: item.dependency,
      days_in_state: 12,
      deadline_days_remaining: 8,
      expected_recovery: item.expected_recovery,
      stages: [
        { label: "Patient", status: "complete", owner: "Facility" },
        { label: "Procedure", status: "complete", owner: "Facility" },
        { label: "Coding", status: item.current_state === "Coding Review" ? "current" : "complete", owner: "Coding Team" },
        { label: "Claim", status: "complete", owner: "AR Specialist" },
        { label: item.current_state, status: "current", owner: item.owner },
        { label: "Resolution", status: "next", owner: item.owner },
        { label: "Payment", status: "pending", owner: "Payer" },
      ],
    },
  }));

function formatMoney(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return `$${value}`;
}

async function fetchPortfolio() {
  if (window.location.protocol === "file:") {
    return fallbackPortfolio;
  }
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
    portfolioState = fallbackPortfolio;
    renderOsLanding(portfolioState.portfolio_snapshot.operator_os_landing);
    renderRoles(portfolioState.portfolio_snapshot.persona_experiences);
    renderPersona(selectedRole);
    mondayPanel.insertAdjacentHTML("beforeend", `<p><strong>Local fallback:</strong> ${error.message}</p>`);
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
