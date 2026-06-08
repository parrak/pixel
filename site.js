const metricsNode = document.getElementById("demoMetrics");
const recoveryMetricsNode = document.getElementById("recoveryMetrics");
const roleList = document.getElementById("roleList");
const personaPanel = document.getElementById("personaPanel");
const graphPanel = document.getElementById("recommendationPanel");
const timelinePanel = document.getElementById("decisionPanel");
const outcomePanel = document.getElementById("outcomePanel");
const commandPrimaryTabs = document.getElementById("commandPrimaryTabs");
const commandPrimaryPanel = document.getElementById("commandPrimaryPanel");
const commandTabs = document.getElementById("commandTabs");
const commandTabPanel = document.getElementById("commandTabPanel");

let portfolioState = null;
let selectedRole = "biller";
let selectedWorkObjectId = null;

const fallbackPortfolio = {
  portfolio_snapshot: {
    operator_os_landing: {
      revenue_at_risk: "2500000.00",
      open_work: 126,
      critical_appeals: 14,
      authorizations_at_risk: 8,
      coding_reviews_pending: 22,
    },
    revenue_recovery_command_center: {
      metrics: {
        revenue_at_risk: "2500000.00",
        recoverable_revenue: "1625000.00",
        appeals_in_progress: 81,
        claims_near_deadline: 98,
        recovered_this_month: "506597.70",
      },
      work_today: [
        { claim_id: "RR-CLM-0104", payer: "United", denial_type: "Medical Necessity", expected_recovery: "12500.00", owner: "Daniel Ortiz", deadline_days: 4, status: "follow_up" },
        { claim_id: "RR-CLM-0118", payer: "Aetna", denial_type: "Missing Documentation", expected_recovery: "9400.00", owner: "Sarah Chen", deadline_days: 6, status: "appeal_in_progress" },
      ],
      money_trapped: [
        { claim_id: "RR-CLM-0104", payer: "United", revenue_at_risk: "12500.00", expected_recovery: "12500.00", status: "blocked" },
        { claim_id: "RR-CLM-0142", payer: "BCBS", revenue_at_risk: "10200.00", expected_recovery: "7140.00", status: "appeal_in_progress" },
      ],
      escalate: [
        { claim_id: "RR-CLM-0104", payer: "United", expected_recovery: "12500.00", owner: "Daniel Ortiz", deadline_days: 4 },
      ],
      blocked: [
        { claim_id: "RR-CLM-0104", payer: "United", expected_recovery: "12500.00", owner: "Daniel Ortiz", status: "blocked" },
      ],
    },
    denial_recovery_factory: {
      denials: [
        { denial_id: "DEN-RR-001", denial_type: "Medical Necessity", payer: "United", financial_impact: "4250.00", status: "appeal_in_progress", owner: "Sarah Chen", deadline: "8 days" },
      ],
      supported_types: ["Missing Documentation", "Medical Necessity", "Authorization Denial", "Coding Denial", "Timely Filing", "Eligibility", "COB"],
    },
    appeal_workspace: {
      appeals: [
        { appeal_id: "APP-RR-001", submission_status: "ready_to_submit", appeal_package: { status: "ready", artifacts: ["Appeal Packet", "Cover Letter", "Evidence Summary"] }, denial: { payer: "United", denial_type: "Medical Necessity", financial_impact: "4250.00" } },
      ],
    },
    evidence_engine: {
      evidence_packets: [
        { claim_id: "RR-CLM-0104", payer: "United", denial_type: "Medical Necessity", packet_readiness: "ready" },
      ],
      evidence_types: ["Operative Note", "Medical Necessity Documentation", "Authorization History", "Payer Rules", "Claim History", "Timeline"],
    },
    payer_playbooks: {
      playbooks: [
        { payer: "United", appeal_success_rate: "68.0%", required_evidence: ["Claim History", "Payer Rules", "Supporting Documentation"] },
        { payer: "Aetna", appeal_success_rate: "64.0%", required_evidence: ["Claim Timeline", "Clinical Documentation"] },
      ],
    },
    similar_recoveries: {
      patterns: [
        { recovery_type: "Medical Necessity", similar_cases: 42, recovery_rate: "61.0%", winning_evidence: ["Clinical Documentation", "Payer Policy"] },
      ],
    },
    recovery_outcome_tracking: {
      rollup: { recovered_revenue: "506597.70", recovery_count: 104 },
      recoveries: [
        { claim_id: "RR-CLM-0081", payer: "Humana", recovered_revenue: "6200.00", time_to_resolution: "21 days" },
      ],
    },
    persona_experiences: {},
    work_objects: [],
  },
};

fallbackPortfolio.portfolio_snapshot.persona_experiences = buildFallbackPersonas();
fallbackPortfolio.portfolio_snapshot.work_objects = buildFallbackWorkObjects(fallbackPortfolio.portfolio_snapshot.persona_experiences);

function buildFallbackPersonas() {
  return {
    coder: persona("coder", "Coding Specialist", "Am I coding this encounter correctly?", ["Patient", "Encounter", "Procedure", "Documentation", "Coding Review", "Charge Capture"], ["My Reviews", "Documentation Gaps", "Coding Queue", "Procedure Explorer", "Completed Reviews", "Knowledge Base"], "WO-FILE-CODING-001", "Arthroscopy encounter coding review", "Encounter", "Coding Review", "Waiting on Coding Review", "1800.00"),
    denial_specialist: persona("denial_specialist", "Denial Specialist", "Which denials can I recover today?", ["Claim", "Denial", "Appeal", "Evidence"], ["My Denials", "Appeals", "Evidence", "Payer Playbooks", "Completed Recoveries"], "WO-FILE-DENIAL-001", "United medical necessity appeal", "Denial", "Appeal", "Waiting on Payer", "4250.00"),
    biller: persona("biller", "AR Specialist", "Which balances can I recover or escalate?", ["Account", "Claim", "Balance", "Recovery Workflow"], ["My AR Queue", "Escalations", "High-Dollar Accounts", "Underpayments", "Completed Recoveries"], "WO-FILE-AR-001", "90+ day no-payment follow-up", "Account", "Recovery Workflow", "Waiting on Payer", "12500.00"),
    auth_specialist: persona("auth_specialist", "Authorization Specialist", "Which scheduled procedures are missing authorization work?", ["Scheduled Procedure", "Authorization", "Requirements"], ["Pending Auths", "Missing Requirements", "Expiring Auths", "Escalations"], "WO-FILE-AUTH-001", "Missing authorization before scheduled case", "Scheduled Procedure", "Authorization", "Waiting on Authorization", "6200.00"),
    manager: persona("manager", "Manager", "Where should I intervene to unblock teams?", ["Teams", "Queues", "Capacity", "Productivity"], ["Operations", "Assignments", "Escalations", "Blockers", "Team Performance"], "WO-FILE-AR-001", "90+ day no-payment follow-up", "Account", "Recovery Workflow", "Waiting on Payer", "12500.00"),
    vp_revenue_cycle: persona("vp_revenue_cycle", "VP Revenue Cycle", "Which operational bottlenecks are putting revenue at risk?", ["Revenue", "Risk", "Operational Bottlenecks"], ["Operational Health", "Revenue At Risk", "Payer Performance", "Interventions"], "WO-FILE-DENIAL-001", "United medical necessity appeal", "Denial", "Appeal", "Waiting on Payer", "4250.00"),
  };
}

function persona(role, label, question, primaryObjects, navigation, id, title, primaryObject, currentState, dependency, expectedRecovery) {
  const item = { work_object_id: id, title, primary_object: primaryObject, current_state: currentState, expected_recovery: expectedRecovery, owner: label, dependency, priority: "urgent", deadline_days_remaining: 8 };
  return {
    role,
    label,
    operator_question: question,
    primary_objects: primaryObjects,
    navigation,
    metrics: { open_work: role === "manager" || role === "vp_revenue_cycle" ? 126 : 7, blocked_work: 7, urgent_work: 3 },
    my_work: [item],
    my_queue: [item],
    todays_priorities: [item],
    blocked_work: [item],
    recommended_actions: [{ work_object_id: id, current_state: currentState, next_state: "Resolution", action: "Review evidence, complete next payer action, and record outcome.", dependency }],
  };
}

function buildFallbackWorkObjects(personas) {
  return Object.values(personas)
    .flatMap((item) => item.my_work)
    .filter((item, index, items) => items.findIndex((candidate) => candidate.work_object_id === item.work_object_id) === index)
    .map((item) => ({
      work_object_id: item.work_object_id,
      title: item.title,
      outcome: { status: "Pending", financial_result: "0.00", impact_summary: "Waiting for operator action." },
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
}

function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `$${value}`;
}

async function fetchPortfolio() {
  if (window.location.protocol === "file:") return fallbackPortfolio;
  const response = await fetch("/api/summary");
  if (!response.ok) throw new Error("Failed to load synthetic portfolio");
  return response.json();
}

async function bootDemo() {
  try {
    portfolioState = await fetchPortfolio();
  } catch (error) {
    portfolioState = fallbackPortfolio;
  }
  selectedWorkObjectId = currentPersona().my_work[0]?.work_object_id;
  renderAll();
}

function snapshot() {
  return portfolioState.portfolio_snapshot;
}

function currentPersona() {
  return snapshot().persona_experiences[selectedRole] || Object.values(snapshot().persona_experiences)[0];
}

function selectedWorkObject() {
  const id = selectedWorkObjectId || currentPersona().my_work[0]?.work_object_id;
  return snapshot().work_objects.find((work) => work.work_object_id === id) || snapshot().work_objects[0];
}

function renderAll() {
  renderMondayMetrics(snapshot().operator_os_landing);
  renderPersonaPanel(currentPersona());
  renderRecoveryMetrics(snapshot().revenue_recovery_command_center?.metrics || {});
  renderRoles(snapshot().persona_experiences);
  renderPrimaryTabs("my_work");
  renderSelectedWorkObject();
  renderCommandTabs("today");
}

function renderMondayMetrics(landing) {
  metricsNode.innerHTML = metric("Revenue at risk", formatMoney(landing.revenue_at_risk)) +
    metric("Open work", landing.open_work) +
    metric("Critical appeals", landing.critical_appeals) +
    metric("Authorizations at risk", landing.authorizations_at_risk) +
    metric("Coding reviews pending", landing.coding_reviews_pending);
}

function renderRecoveryMetrics(metrics) {
  recoveryMetricsNode.innerHTML =
    metric("Revenue At Risk", formatMoney(metrics.revenue_at_risk)) +
    metric("Recoverable Revenue", formatMoney(metrics.recoverable_revenue)) +
    metric("Appeals In Progress", metrics.appeals_in_progress ?? "-") +
    metric("Near Deadline", metrics.claims_near_deadline ?? "-") +
    metric("Recovered This Month", formatMoney(metrics.recovered_this_month));
}

function metric(label, value) {
  return `<div class="metric-tile"><span>${label}</span><strong>${value}</strong></div>`;
}

function renderPersonaPanel(persona) {
  const current = persona.my_work[0] || persona.my_queue[0] || {};
  personaPanel.innerHTML = `
    <span class="eyebrow">Role-Specific OS</span>
    <h2>${persona.label}</h2>
    <p>${persona.operator_question}</p>
    <div class="persona-layout-static">
      ${personaBlock("Primary Objects", persona.primary_objects.join(" → "))}
      ${personaBlock("Navigation", persona.navigation.join(" · "))}
      ${personaBlock("Queue State", `${persona.metrics.open_work ?? "-"} open work · ${persona.metrics.blocked_work ?? "-"} blocked · ${persona.metrics.urgent_work ?? "-"} urgent`)}
      ${personaBlock("Current Object", `${current.title || "No current work"}<br/>${current.primary_object || "Work Object"} · ${current.current_state || "-"} · waiting on ${current.dependency || "-"}`)}
    </div>
  `;
}

function personaBlock(label, value) {
  return `<div><span>${label}</span><p>${value}</p></div>`;
}

function renderRoles(personas) {
  roleList.innerHTML = "";
  Object.values(personas).forEach((persona) => {
    const item = document.createElement("button");
    item.className = `queue-item${persona.role === selectedRole ? " is-active" : ""}`;
    item.innerHTML = `<strong>${persona.label}</strong><p>${persona.operator_question}</p><p>${persona.navigation.join(" · ")}</p>`;
    item.addEventListener("click", () => {
      selectedRole = persona.role;
      selectedWorkObjectId = persona.my_work[0]?.work_object_id || persona.my_queue[0]?.work_object_id;
      renderAll();
    });
    roleList.appendChild(item);
  });
}

function renderPrimaryTabs(active) {
  const tabs = [
    ["my_work", "My Work"],
    ["my_queue", "My Queue"],
    ["priorities", "Today's Priorities"],
    ["blocked", "Blocked Work"],
    ["actions", "Recommended Actions"],
    ["work_today", "Work Today"],
    ["money_trapped", "Money Trapped"],
  ];
  commandPrimaryTabs.innerHTML = tabs.map(([id, label]) => `<button class="tab-button${id === active ? " is-active" : ""}" data-tab="${id}">${label}</button>`).join("");
  commandPrimaryTabs.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => renderPrimaryTabs(button.dataset.tab)));
  renderPrimaryPanel(active);
}

function renderPrimaryPanel(active) {
  const persona = currentPersona();
  const recovery = snapshot().revenue_recovery_command_center || {};
  if (active === "my_queue") {
    renderSelectableWorkTable(commandPrimaryPanel, persona.my_queue || [], ["title", "primary_object", "current_state", "owner", "expected_recovery"]);
  } else if (active === "priorities") {
    renderSelectableWorkTable(commandPrimaryPanel, persona.todays_priorities || [], ["title", "priority", "deadline_days_remaining", "expected_recovery"]);
  } else if (active === "blocked") {
    renderSelectableWorkTable(commandPrimaryPanel, persona.blocked_work || [], ["title", "dependency", "current_state", "expected_recovery"]);
  } else if (active === "actions") {
    renderTable(commandPrimaryPanel, persona.recommended_actions || [], ["action", "current_state", "next_state", "dependency"]);
  } else if (active === "work_today") {
    renderTable(commandPrimaryPanel, recovery.work_today || [], ["claim_id", "payer", "denial_type", "expected_recovery", "owner", "deadline_days"]);
  } else if (active === "money_trapped") {
    renderTable(commandPrimaryPanel, recovery.money_trapped || [], ["claim_id", "payer", "denial_type", "revenue_at_risk", "expected_recovery", "status"]);
  } else {
    renderSelectableWorkTable(commandPrimaryPanel, persona.my_work || [], ["title", "primary_object", "current_state", "dependency", "expected_recovery"]);
  }
}

function renderSelectedWorkObject() {
  renderWorkObject(selectedWorkObject(), currentPersona());
}

function renderSelectableWorkTable(node, rows, fields) {
  if (!rows || !rows.length) {
    node.innerHTML = "<p>No items in this synthetic view.</p>";
    return;
  }
  const safeRows = rows.slice(0, 14);
  node.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>${fields.map((field) => `<th>${labelize(field)}</th>`).join("")}</tr></thead>
        <tbody>
          ${safeRows.map((row) => `<tr class="selectable-row" data-work-object-id="${row.work_object_id || ""}">${fields.map((field) => `<td>${formatCell(row[field])}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;
  node.querySelectorAll(".selectable-row").forEach((row) => row.addEventListener("click", () => {
    if (row.dataset.workObjectId) {
      selectedWorkObjectId = row.dataset.workObjectId;
      renderSelectedWorkObject();
    }
  }));
}

function renderWorkObject(workObject, persona) {
  if (!workObject) {
    graphPanel.innerHTML = "<p>No work object available.</p>";
    timelinePanel.innerHTML = "<p>No timeline available.</p>";
    outcomePanel.innerHTML = "<p>No outcome available.</p>";
    return;
  }
  const graph = workObject.workflow_graph || {};
  graphPanel.innerHTML = `
    <strong>${workObject.title}</strong>
    <p><strong>Current State:</strong> ${graph.current_state || "-"}</p>
    <p><strong>Owner:</strong> ${graph.owner || "-"}</p>
    <p><strong>Waiting On:</strong> ${graph.waiting_on || "-"}</p>
    <p><strong>Days In State:</strong> ${graph.days_in_state || "-"}</p>
    <p><strong>Deadline:</strong> ${graph.deadline_days_remaining || "-"} days remaining</p>
    <p><strong>Expected Recovery:</strong> ${formatMoney(graph.expected_recovery)}</p>
    <div class="workflow-graph">${(graph.stages || []).map(renderStage).join("")}</div>
  `;
  timelinePanel.innerHTML = `<strong>What happened</strong><ul>${(workObject.timeline || []).map((event) => `<li><strong>${event.label}:</strong> ${event.detail}</li>`).join("")}</ul>`;
  outcomePanel.innerHTML = `
    <strong>Outcome + Memory</strong>
    <p><strong>Status:</strong> ${workObject.outcome?.status || "Pending"}</p>
    <p><strong>Financial result:</strong> ${formatMoney(workObject.outcome?.financial_result || "0.00")}</p>
    <p><strong>Memory:</strong> ${workObject.institutional_memory?.[0]?.summary || "Next action will create institutional memory."}</p>
    <ul>${(persona.recommended_actions || []).map((action) => `<li>${action.action}</li>`).join("")}</ul>
  `;
}

function renderStage(stage) {
  return `<div class="graph-node graph-${stage.status}"><strong>${stage.label}</strong><span>${stage.owner}</span></div>`;
}

function renderCommandTabs(active) {
  const tabs = [
    ["today", "Today"],
    ["denials", "Denial Factory"],
    ["appeals", "Appeals"],
    ["evidence", "Evidence"],
    ["playbooks", "Payer Playbooks"],
    ["outcomes", "Outcomes"],
  ];
  commandTabs.innerHTML = tabs.map(([id, label]) => `<button class="tab-button${id === active ? " is-active" : ""}" data-tab="${id}">${label}</button>`).join("");
  commandTabs.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => renderCommandTabs(button.dataset.tab)));
  renderTabPanel(active);
}

function renderTabPanel(active) {
  const data = snapshot();
  if (active === "denials") {
    renderTable(commandTabPanel, data.denial_recovery_factory?.denials || [], ["denial_id", "denial_type", "payer", "financial_impact", "owner", "status"]);
  } else if (active === "appeals") {
    renderTable(commandTabPanel, (data.appeal_workspace?.appeals || []).map((item) => ({ appeal_id: item.appeal_id, payer: item.denial?.payer, denial_type: item.denial?.denial_type, package_status: item.appeal_package?.status, submission_status: item.submission_status })), ["appeal_id", "payer", "denial_type", "package_status", "submission_status"]);
  } else if (active === "evidence") {
    renderTable(commandTabPanel, data.evidence_engine?.evidence_packets || [], ["claim_id", "payer", "denial_type", "packet_readiness"]);
  } else if (active === "playbooks") {
    renderTable(commandTabPanel, data.payer_playbooks?.playbooks || [], ["payer", "appeal_success_rate", "required_evidence"]);
  } else if (active === "outcomes") {
    renderTable(commandTabPanel, data.recovery_outcome_tracking?.recoveries || [], ["claim_id", "payer", "recovered_revenue", "time_to_resolution"]);
  } else {
    renderTable(commandTabPanel, data.revenue_recovery_command_center?.escalate || [], ["claim_id", "payer", "expected_recovery", "owner", "deadline_days"]);
  }
}

function renderTable(node, rows, fields) {
  if (!rows || !rows.length) {
    node.innerHTML = "<p>No items in this synthetic view.</p>";
    return;
  }
  const safeRows = rows.slice(0, 12);
  node.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr>${fields.map((field) => `<th>${labelize(field)}</th>`).join("")}</tr></thead>
        <tbody>
          ${safeRows.map((row) => `<tr>${fields.map((field) => `<td>${formatCell(row[field])}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function labelize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatCell(value) {
  if (Array.isArray(value)) return value.join(" · ");
  if (value && typeof value === "object") return Object.values(value).join(" · ");
  if (value === undefined || value === null || value === "") return "-";
  return String(value);
}

bootDemo();
